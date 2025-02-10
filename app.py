import streamlit as st
import os
from main import graph
from langchain_core.messages import AIMessage, HumanMessage
import config
st.set_page_config(layout='wide', page_title='Content-G Chatbot', page_icon='🍐')


language_dict = {"English":"en",
    "Afrikaans": "af", "Amharic": "am", "Arabic": "ar", "Azerbaijani": "az", "Belarusian": "be", "Bulgarian": "bg", "Bengali": "bn", "Bosnian": "bs", "Catalan": "ca", "Cebuano": "ceb", "Corsican": "co", "Czech": "cs", "Welsh": "cy", "Danish": "da", "German": "de", "Greek": "el", "Esperanto": "eo", "Spanish": "es", "Estonian": "et", "Basque": "eu", "Persian": "fa", "Finnish": "fi", "French": "fr", "Frisian": "fy", "Irish": "ga", "Scots Gaelic": "gd", "Galician": "gl", "Gujarati": "gu", "Hausa": "ha", "Hawaiian": "haw", "Hindi": "hi", "Hmong": "hmn", "Croatian": "hr", "Haitian Creole": "ht", "Hungarian": "hu", "Armenian": "hy", "Indonesian": "id", "Igbo": "ig", "Icelandic": "is", "Italian": "it", "Hebrew": "he", "Japanese": "ja", "Javanese": "jv", "Georgian": "ka", "Kazakh": "kk", "Khmer": "km", "Kannada": "kn", "Korean": "ko", "Kurdish": "ku", "Kyrgyz": "ky", "Latin": "la", "Luxembourgish": "lb", "Lao": "lo", "Lithuanian": "lt", "Latvian": "lv", "Malagasy": "mg", "Maori": "mi", "Macedonian": "mk", "Malayalam": "ml", "Mongolian": "mn", "Marathi": "mr", "Malay": "ms", "Maltese": "mt", "Burmese": "my", "Nepali": "ne", "Dutch": "nl", "Norwegian": "no", "Nyanja": "ny", "Odia": "or", "Punjabi": "pa", "Polish": "pl", "Pashto": "ps", "Portuguese": "pt", "Romanian": "ro", "Russian": "ru", "Sindhi": "sd", "Sinhala": "si", "Slovak": "sk", "Slovenian": "sl", "Samoan": "sm", "Shona": "sn", "Somali": "so", "Albanian": "sq", "Serbian": "sr", "Sesotho": "st", "Sundanese": "su", "Swedish": "sv", "Swahili": "sw", "Tamil": "ta", "Telugu": "te", "Tajik": "tg", "Thai": "th", "Tagalog": "tl", "Turkish": "tr", "Uyghur": "ug", "Ukrainian": "uk", "Urdu": "ur", "Uzbek": "uz", "Vietnamese": "vi", "Xhosa": "xh", "Yiddish": "yi", "Yoruba": "yo", "Chinese": "zh", "Zulu": "zu"
}

# Initialize session state
if 'message_history' not in st.session_state:
    st.session_state.message_history = [AIMessage(content="Hiya, I'm the Content-G chatbot. How can I help?")]
if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = ""
if 'video_ready' not in st.session_state:
    st.session_state.video_ready = False  
if 'default_language' not in st.session_state:
    st.session_state.default_language = "English"  # Default to English
if 'target_language' not in st.session_state:
    st.session_state.target_language = language_dict[st.session_state.default_language]
left_col, main_col, right_col = st.columns([1, 2, 1])


with left_col:
    if st.button('Clear Chat'):
        st.session_state.message_history = []
        st.session_state.pdf_path = ""
        st.session_state.video_ready = False
    selected_language = st.selectbox("Select Language", list(language_dict.keys()), index=list(language_dict.keys()).index(st.session_state.default_language))
    st.session_state.default_language = selected_language
    st.session_state.target_language = language_dict[selected_language]
    config.target_language = language_dict[selected_language]


# 2. File uploader & Chat input
with main_col:
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file is not None:
        os.makedirs("uploads", exist_ok=True)
        save_path = os.path.join("uploads", uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"Uploaded successfully: {uploaded_file.name}")
        st.session_state.pdf_path = save_path

    user_input = st.chat_input("Type here...")

    if not user_input and st.session_state.pdf_path:
        user_input = st.session_state.pdf_path
        st.session_state.pdf_path = ""

    if user_input:
        st.session_state.message_history.append(HumanMessage(content=user_input))
        response = graph.invoke({
            'messages': st.session_state.message_history
        })
        st.session_state.message_history = response['messages']

    # Display messages with the most recent at the top
    for message in reversed(st.session_state.message_history):
        message_box = st.chat_message('assistant' if isinstance(message, AIMessage) else 'user')
        message_box.markdown(message.content)

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
