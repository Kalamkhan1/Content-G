from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from typing import Annotated

class OrderState(TypedDict):
    messages: Annotated[list, add_messages]  # Conversation messages
    finished: bool  # Whether the conversation is finished
