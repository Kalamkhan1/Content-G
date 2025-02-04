from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json 
from orderState import OrderState
from chrome.Chrome import db
from models import llm_with_tools
from langchain_core.messages import AIMessage,ToolMessage
from utils import WELCOME_MSG,TASK_SYSINT,split_script
from tools import create_script_animate


def upload_and_rag_node(state: OrderState) -> OrderState:
    """Handles both document uploads and retrieval-augmented generation based on tool names."""
    last_msg = state["messages"][-1]
    user_input=last_msg.content
    id = last_msg.id
    function_call = last_msg.additional_kwargs["function_call"]
    arguments_json = function_call.get("arguments", "{}")
    arguments_dict = json.loads(arguments_json)
    file_path = str(arguments_dict.get("file_path", ""))
    

    try:
        # Define the prompt template for summarization
        prompt_template = PromptTemplate(template="Summarize the uploaded document: {context}")
        
        # Check if the message contains any tool calls and process based on tool name
        if hasattr(last_msg, "tool_calls"):
            for tool in last_msg.tool_calls:
                if tool["name"] == "upload_doc":
                    # Convert the user input into a raw string for file pat
                    print(f"Processing file: {file_path}")

                    try:
                        if file_path.endswith(".pdf"):
                            loader = PyPDFLoader(file_path)
                            documents = loader.load()  # Extract text as a list of documents
                            text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000,chunk_overlap=300)
                            chunks = text_splitter.split_documents(documents)
                            db.add_documents(chunks)  

                        else:
                            # Handle plain-text files
                            with open(file_path, "r", encoding="utf-8") as file:
                                document_content = file.read()

                       
                            db.add_documents([{"content": document_content}])

                        
                        # Respond with the summary of the document
                        return state | {"messages": [ToolMessage(content=f"Document uploaded successfully!", tool_call_id=id)]}

                    except Exception as e:
                        return state | {"messages": [ToolMessage(content=f"Error uploading document: {str(e)}", tool_call_id=id)]}

                elif tool["name"] == "query_doc":
                    retriever = db.as_retriever()

                    
                    qa_chain = RetrievalQA.from_chain_type(
                        llm=llm_with_tools,  # Use LLM with tools for RAG processing
                        retriever=retriever,
                        chain_type_kwargs={"prompt": prompt_template},
                    )

                    # Run the query and get the response
                    response = qa_chain.invoke({"query": user_input})
                    return state | {"messages": [ToolMessage(content=response,tool_call_id=id)]}

        else:
            # If no tools were invoked, return an error or human response
            return state | {"messages": [ToolMessage(content="No tool calls detected. Please upload a document or ask a query.")]}
    
    except Exception as e:
        # If an error occurs during processing, notify the user
        return state | {"messages": [ToolMessage(content=f"Error processing request: {str(e)}")]}




def chatbot_with_tools(state: OrderState) -> OrderState:
    """The chatbot with tools. A simple wrapper around the model's own chat interface."""
    defaults = {"finished": False,}
    
    if state["messages"]:
        # Get the message from the state and process based on response_count
        sum_output = llm_with_tools.invoke([TASK_SYSINT] + state["messages"])

        
    else:
        sum_output = AIMessage(content=WELCOME_MSG)


    # Set up some defaults if not already set, then pass through the provided state,
    # overriding only the "messages" field.
    return defaults | state | {"messages": [sum_output]}


def human_node(state: OrderState) -> OrderState:
    """Display the last model message to the user, and receive the user's input."""
    last_msg = state["messages"][-1]
    print("Model:", last_msg.content)
     
    user_input = input("User: ")

    if user_input in {"q", "quit", "exit", "goodbye"}:
        state["finished"] = True

    return state | {"messages": [("user", user_input)]}

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