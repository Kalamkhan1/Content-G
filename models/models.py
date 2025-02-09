from langchain_google_genai import ChatGoogleGenerativeAI

from tools import translate_and_text_to_speech,create_script_animate

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", generation_config={"temperature": 0.2})
tools = [translate_and_text_to_speech,create_script_animate]
llm_with_tools = llm.bind_tools(tools)
