from langchain_google_genai import ChatGoogleGenerativeAI

from tools import translate_and_text_to_speech,create_script_animate

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", generation_config={"temperature": 0.3})
tools = [translate_and_text_to_speech,create_script_animate]
llm_with_tools = llm.bind_tools(tools)
