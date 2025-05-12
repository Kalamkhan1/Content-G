from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json 
from orderState import OrderState
from chrome.Chrome import db
from models import llm_with_tools
from langchain_core.messages import ToolMessage
from utils import TASK_SYSINT,all_docs
from tools import create_script_animate
from langchain.docstore.document import Document
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever


def upload_and_rag_node(state: OrderState) -> OrderState:
    """Handles both document uploads and fusion RAG (semantic + BM25)."""
    last_msg = state["messages"][-1]
    user_input = last_msg.content
    function_call = last_msg.additional_kwargs.get("function_call", {})
    arguments = json.loads(function_call.get("arguments", "{}"))
    file_path = arguments.get("file_path", "")
    prompt_template = PromptTemplate(template="Summarize the uploaded document: {context}")

    # Process tool calls
    if hasattr(last_msg, "tool_calls"):
        for tool in last_msg.tool_calls:
            name = tool["name"]
            call_id = tool.get("id", last_msg.id)

            if name == "upload_doc":
                # --- UPLOAD ---
                try:
                    if file_path.lower().endswith(".pdf"):
                        loader = PyPDFLoader(file_path)
                        docs = loader.load()
                    else:
                        # plain text
                        with open(file_path, "r", encoding="utf-8") as f:
                            text = f.read()
                        docs = [Document(page_content=text, metadata={"source": file_path})]

                    # split into chunks
                    splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=300)
                    chunks = splitter.split_documents(docs)

                    # add to Chroma
                    db.add_documents(chunks)
                    # also keep for BM25
                    all_docs.extend(chunks)

                    return state | {
                        "messages": [
                            ToolMessage(
                                content="Document uploaded successfully!",
                                tool_call_id=call_id,
                            )
                        ]
                    }
                except Exception as e:
                    return state | {
                        "messages": [
                            ToolMessage(
                                content=f"Error uploading document: {e}",
                                tool_call_id=call_id,
                            )
                        ]
                    }

            elif name == "query_doc":
                # --- QUERY / RAG with Fusion ---
                try:
                    # 1) semantic retriever from Chroma
                    semantic_retriever = db.as_retriever(search_kwargs={"k": 5})

                    # 2) BM25 retriever
                    bm25 = BM25Retriever.from_documents(all_docs)
                    bm25.k = 5

                    # 3) fuse them
                    fused = EnsembleRetriever(retrievers=[bm25, semantic_retriever], weights=[0.5, 0.5])

                    # 4) build QA chain
                    qa = RetrievalQA.from_chain_type(
                        llm=llm_with_tools,
                        retriever=fused,
                        chain_type_kwargs={"prompt": prompt_template},
                    )

                    # 5) run
                    answer = qa.invoke({"query": user_input})

                    return state | {
                        "messages": [
                            ToolMessage(
                                content=answer,
                                tool_call_id=call_id,
                            )
                        ]
                    }
                except Exception as e:
                    return state | {
                        "messages": [
                            ToolMessage(
                                content=f"Error during retrieval: {e}",
                                tool_call_id=call_id,
                            )
                        ]
                    }

    # no tool call
    return state | {
        "messages": [
            ToolMessage(
                content="⚠️ No tool call detected. Please upload a document or ask a query.",
                tool_call_id=last_msg.id,
            )
        ]
    }



def chatbot_with_tools(state: OrderState) -> OrderState:
    """The chatbot with tools. A simple wrapper around the model's own chat interface."""
    
    sum_output = llm_with_tools.invoke([TASK_SYSINT] + state["messages"])

    # Set up some defaults if not already set, then pass through the provided state,
    # overriding only the "messages" field.
    return state | {"messages": [sum_output]}


#def human_node(state: OrderState) -> OrderState:
#    """Display the last model message to the user, and receive the user's input."""
#    last_msg = state["messages"][-1]
#    print("Model:", last_msg.content)
#     
#    user_input = input("User: ")
#
#    if user_input in {"q", "quit", "exit", "goodbye"}:
#        state["finished"] = True
#
#    return state | {"messages": [("user", user_input)]}

def builder_node(state: dict) -> dict:
    # Extract the latest tool message
    tool_msg = state.get("messages", [])[-1] if state.get("messages", []) else None
    
    if not tool_msg:
        print("No tool messages in state.")
        return state

    id = tool_msg.id  # Tool message ID for response mapping
    try:
        for tool_call in tool_msg.tool_calls:
            tool_name = tool_call["name"]
            function_call = tool_msg.additional_kwargs.get("function_call", {})
            arguments_json = function_call.get("arguments", "{}")
            arguments_dict = json.loads(arguments_json)

            if tool_name == "create_script_animate":
                script_en = str(arguments_dict.get("script", ""))
                if not script_en:
                    print("this!!")
                    raise ValueError("No valid 'script' found in function arguments.")

                response = create_script_animate(script_en)

                return {
                    "messages": [
                        ToolMessage(content=response, tool_call_id=id)
                    ],
                    "finished": False,
                }

            else:
                raise NotImplementedError(f"Unknown tool call: {tool_name}")

    except Exception as e:
        return {
            "messages": [
                ToolMessage(content=f"Error: {str(e)}", tool_call_id=id)
            ],
            "finished": False,
        }