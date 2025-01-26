from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from tools import run_manim_code,translate_and_text_to_speech

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest")
tools = [run_manim_code,translate_and_text_to_speech]
llm_with_tools = llm.bind_tools(tools)

manim_model = genai.GenerativeModel('gemini-1.5-flash-8b-latest')