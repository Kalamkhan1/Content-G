 
from typing import Literal
from orderState import OrderState
from langgraph.graph import StateGraph, START
from nodes import builder_node,chatbot_with_tools,upload_and_rag_node
import opik


opik.configure(use_local=False)
#def maybe_exit_human_node(state: OrderState) -> Literal["chatbot", "__end__"]:
#    """Route to the chatbot, unless it looks like the user is exiting."""
#    if state.get("finished", False):
#        return END
#    else:
#        return "chatbot"
    
def maybe_route_to_tools(state: OrderState) -> str:
    """Route between chat, tools, or specific nodes."""
    if not (msgs := state.get("messages", [])):
        raise ValueError(f"No messages found when parsing state: {state}")

    # Analyze the last message
    msg = msgs[-1]

    # Check for tool-specific keywords in the tool calls
    if hasattr(msg, "tool_calls"):
        for tool in msg.tool_calls:
            print(tool)
            if tool["name"] == "create_script_animate":
                return "builder"

    return '__end__'



# Initialize the state graph and add the nodes
graph_builder = StateGraph(OrderState)

# Add the nodes, including the new tool_node.
graph_builder.add_node("chatbot", chatbot_with_tools)
graph_builder.add_node("rag", upload_and_rag_node)
graph_builder.add_node("builder", builder_node)
graph_builder.add_edge(START, "rag")
graph_builder.add_edge("rag", "chatbot")
graph_builder.add_conditional_edges("chatbot", maybe_route_to_tools)
graph_builder.add_edge("builder", "chatbot")



graph = graph_builder.compile()

#Image(graph_with_menu.get_graph().draw_mermaid_png())



#state = graph.invoke({"messages": []},config)
