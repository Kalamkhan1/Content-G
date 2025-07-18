from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import json 
from orderState import OrderState
from chrome.Chrome import db
from models import llm_with_tools
from langchain_core.messages import ToolMessage, HumanMessage
from utils import TASK_SYSINT
from tools import create_script_animate
from langchain.docstore.document import Document
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever


def upload_and_rag_node(state: OrderState) -> OrderState:
    """Handles both document uploads and fusion RAG (semantic + BM25)."""
  
    user_input = state["messages"]

    if state['rag_enabled'] == False:
        print("N)))))))))))))))))))))")
        return {
            "messages": 
            user_input  
        }


    user_input = user_input[-1].content

    prompt_template = PromptTemplate(template="Answer the question based on the context provided.\n if no context is provided or if the context is not relevant to the question, then answer the question genuinely and in detail.\n Context :{context}\n\n question: {question}")
    final_prompt = user_input
    try:
        # 1) semantic retriever from Chroma
        raw_docs = db.get(include=["documents", "metadatas"])
        # Convert raw docs to LangChain Document objects
        documents = [
            Document(page_content=doc, metadata=meta)
            for doc, meta in zip(raw_docs["documents"], raw_docs["metadatas"])
        ]

        # BM25 retriever
        bm25_retriever = BM25Retriever.from_documents(documents=documents, k=5)

        # Similarity retriever
        similarity_retriever = db.as_retriever(
            search_type="similarity",
            search_kwargs={'k': 5}
        )

        # Combine with EnsembleRetriever
        ensemble = EnsembleRetriever(
            retrievers=[similarity_retriever, bm25_retriever],
            weights=[0.6, 0.4]
        )
        # Retrieve documents
        docs = ensemble.invoke(user_input)
        print(len(docs))
 
        context = "\n\n".join(doc.page_content for doc in docs)

        # 8) Format the prompt with the context and user question
        final_prompt = prompt_template.format(context=context, question=user_input)
        print(final_prompt)
        # 9) Return the context and prompt
        return {
                    "messages": 
                      final_prompt  
                }

    except Exception as e:
        print("another NOOOOOOOOOOOOOOOOOOOO",e)
        return {
                    "messages": 
                      final_prompt  
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