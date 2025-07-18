import streamlit as st
import os
from main import graph
from langchain_core.messages import AIMessage, HumanMessage , ToolMessage
from translatepy import Translator
from translatepy.exceptions import NoResult
from upload import ingest_document
from opik.integrations.langchain import OpikTracer

tracer = OpikTracer(graph=graph.get_graph(xray=True))


def translate(script: str, target_language: str) -> str:  
    translator = Translator()
    try:
        translated_result = translator.translate(script, target_language)
        translated_text = translated_result.result  # Get translated text
        return translated_text
    except NoResult:
        return script


st.set_page_config(layout='wide', page_title='Content-G', page_icon='🍐')


language_dict = {"English":"en",
    "Afrikaans": "af", "Amharic": "am", "Arabic": "ar", "Azerbaijani": "az", "Belarusian": "be", "Bulgarian": "bg", "Bengali": "bn", "Bosnian": "bs", "Catalan": "ca", "Cebuano": "ceb", "Corsican": "co", "Czech": "cs", "Welsh": "cy", "Danish": "da", "German": "de", "Greek": "el", "Esperanto": "eo", "Spanish": "es", "Estonian": "et", "Basque": "eu", "Persian": "fa", "Finnish": "fi", "French": "fr", "Frisian": "fy", "Irish": "ga", "Scots Gaelic": "gd", "Galician": "gl", "Gujarati": "gu", "Hausa": "ha", "Hawaiian": "haw", "Hindi": "hi", "Hmong": "hmn", "Croatian": "hr", "Haitian Creole": "ht", "Hungarian": "hu", "Armenian": "hy", "Indonesian": "id", "Igbo": "ig", "Icelandic": "is", "Italian": "it", "Hebrew": "he", "Japanese": "ja", "Javanese": "jv", "Georgian": "ka", "Kazakh": "kk", "Khmer": "km", "Kannada": "kn", "Korean": "ko", "Kurdish": "ku", "Kyrgyz": "ky", "Latin": "la", "Luxembourgish": "lb", "Lao": "lo", "Lithuanian": "lt", "Latvian": "lv", "Malagasy": "mg", "Maori": "mi", "Macedonian": "mk", "Malayalam": "ml", "Mongolian": "mn", "Marathi": "mr", "Malay": "ms", "Maltese": "mt", "Burmese": "my", "Nepali": "ne", "Dutch": "nl", "Norwegian": "no", "Nyanja": "ny", "Odia": "or", "Punjabi": "pa", "Polish": "pl", "Pashto": "ps", "Portuguese": "pt", "Romanian": "ro", "Russian": "ru", "Sindhi": "sd", "Sinhala": "si", "Slovak": "sk", "Slovenian": "sl", "Samoan": "sm", "Shona": "sn", "Somali": "so", "Albanian": "sq", "Serbian": "sr", "Sesotho": "st", "Sundanese": "su", "Swedish": "sv", "Swahili": "sw", "Tamil": "ta", "Telugu": "te", "Tajik": "tg", "Thai": "th", "Tagalog": "tl", "Turkish": "tr", "Uyghur": "ug", "Ukrainian": "uk", "Urdu": "ur", "Uzbek": "uz", "Vietnamese": "vi", "Xhosa": "xh", "Yiddish": "yi", "Yoruba": "yo", "Chinese": "zh", "Zulu": "zu"
}

# Initialize session state
if 'message_history' not in st.session_state:
    st.session_state.message_history = [AIMessage(content="Hiya, I'm your Content-G. How can I help?")]
if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = ""
if 'video_ready' not in st.session_state:
    st.session_state.video_ready = False  
if 'default_language' not in st.session_state:
    st.session_state.default_language = "English"  # Default to English
if 'target_language' not in st.session_state:
    st.session_state.target_language = language_dict[st.session_state.default_language]
if 'rag' not in st.session_state:
    st.session_state.rag = False
left_col, main_col, right_col = st.columns([1, 2, 1])


with left_col:
    if st.button('Clear Chat'):
        st.session_state.message_history = []
        st.session_state.pdf_path = ""
        st.session_state.video_ready = False
    selected_language = st.selectbox("Select Language", list(language_dict.keys()), index=list(language_dict.keys()).index(st.session_state.default_language))
    st.session_state.default_language = selected_language
    st.session_state.target_language = language_dict[selected_language]
    with open("config.txt", "w") as file:
        file.write(language_dict[selected_language])


# 2. File uploader & Chat input
with main_col:
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file is not None:
        os.makedirs("uploads", exist_ok=True)
        save_path = os.path.join("uploads", uploaded_file.name)

        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Ingest the document into Chroma DB
        ingest_document(save_path)
        st.session_state.rag = True
        print(st.session_state.rag)

        st.success(f"Uploaded and ingested successfully: {uploaded_file.name}")

    user_input = st.chat_input("Type here...")

    if user_input:
        st.session_state.message_history.append(HumanMessage(content=user_input))
        conf = {"recursion_limit": 100,"callbacks": [tracer]}
        response = graph.invoke({
            'messages': st.session_state.message_history,
            'rag_enabled':st.session_state.rag
        },conf)
        st.session_state.message_history = response['messages']

    # Display messages with the most recent at the top
    for message in reversed(st.session_state.message_history):
        if isinstance(message, ToolMessage) or isinstance(message, ToolMessage):
            continue  
        message_box = st.chat_message('assistant' if isinstance(message, AIMessage) else 'user')
        script=translate(message.content,st.session_state.target_language)
        if st.session_state.target_language == "en":
            script=f"{script}"
        else:
            script=f"{script}\n\n{message.content}"
        message_box.markdown(script)

video_path = os.path.join(os.getcwd(), "final_output.mp4")

# 3. Video Display in Right Column
with right_col:
    st.markdown("### 🎥 Generated Video")

    if not st.session_state.video_ready:
        st.warning("Waiting for video to be generated...")
        
        # Periodic check without blocking execution
        if os.path.exists(video_path):
            st.session_state.video_ready = True
            st.rerun()  # Rerun app when video is ready

    if st.session_state.video_ready:
        st.video(video_path)
