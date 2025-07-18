from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import os
from main import graph
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from translatepy import Translator
from translatepy.exceptions import NoResult

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for flash messages

app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), "Uploads")
app.config['VIDEO_FOLDER'] = os.getcwd()  # Assumes final_output.mp4 is in the current directory

# Global state variables (for simplicity)
chat_history = []   # List of tuples: (role, message)
pdf_path = ""
video_ready = False
default_language = "English"
language_dict = {
    "English": "en",
    "Afrikaans": "af", "Amharic": "am", "Arabic": "ar", "Azerbaijani": "az", "Belarusian": "be", "Bulgarian": "bg",
    "Bengali": "bn", "Bosnian": "bs", "Catalan": "ca", "Cebuano": "ceb", "Corsican": "co", "Czech": "cs", "Welsh": "cy",
    "Danish": "da", "German": "de", "Greek": "el", "Esperanto": "eo", "Spanish": "es", "Estonian": "et", "Basque": "eu",
    "Persian": "fa", "Finnish": "fi", "French": "fr", "Frisian": "fy", "Irish": "ga", "Scots Gaelic": "gd",
    "Galician": "gl", "Gujarati": "gu", "Hausa": "ha", "Hawaiian": "haw", "Hindi": "hi", "Hmong": "hmn",
    "Croatian": "hr", "Haitian Creole": "ht", "Hungarian": "hu", "Armenian": "hy", "Indonesian": "id", "Igbo": "ig",
    "Icelandic": "is", "Italian": "it", "Hebrew": "he", "Japanese": "ja", "Javanese": "jv", "Georgian": "ka",
    "Kazakh": "kk", "Khmer": "km", "Kannada": "kn", "Korean": "ko", "Kurdish": "ku", "Kyrgyz": "ky", "Latin": "la",
    "Luxembourgish": "lb", "Lao": "lo", "Lithuanian": "lt", "Latvian": "lv", "Malagasy": "mg", "Maori": "mi",
    "Macedonian": "mk", "Malayalam": "ml", "Mongolian": "mn", "Marathi": "mr", "Malay": "ms", "Maltese": "mt",
    "Burmese": "my", "Nepali": "ne", "Dutch": "nl", "Norwegian": "no", "Nyanja": "ny", "Odia": "or", "Punjabi": "pa",
    "Polish": "pl", "Pashto": "ps", "Portuguese": "pt", "Romanian": "ro", "Russian": "ru", "Sindhi": "sd",
    "Sinhala": "si", "Slovak": "sk", "Slovenian": "sl", "Samoan": "sm", "Shona": "sn", "Somali": "so", "Albanian": "sq",
    "Serbian": "sr", "Sesotho": "st", "Sundanese": "su", "Swedish": "sv", "Swahili": "sw", "Tamil": "ta", "Telugu": "te",
    "Tajik": "tg", "Thai": "th", "Tagalog": "tl", "Turkish": "tr", "Uyghur": "ug", "Ukrainian": "uk", "Urdu": "ur",
    "Uzbek": "uz", "Vietnamese": "vi", "Xhosa": "xh", "Yiddish": "yi", "Yoruba": "yo", "Chinese": "zh", "Zulu": "zu"
}
target_language = language_dict[default_language]

def translate_text(script, target_language):
    if target_language == "en":
        return script  # Skip translation if target is English
    translator = Translator()
    try:
        result = translator.translate(script, target_language)
        return result.result
    except NoResult:
        return script

def write_config_lang_code(lang_code):
    with open("config.txt", "w") as f:
        f.write(lang_code)

@app.route('/', methods=['GET', 'POST'])
def index():
    global chat_history, pdf_path, video_ready, default_language, target_language
    if request.method == 'POST':
        new_lang = request.form.get('language_select')
        if new_lang:
            default_language = new_lang
            target_language = language_dict[new_lang]
            write_config_lang_code(target_language)
            flash(f"Language changed to {default_language}")

        if 'file' in request.files and request.files['file'].filename != "":
            file = request.files['file']
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            pdf_path = file_path
            flash(f"File uploaded successfully: {file.filename}")
            chat_history.append(("user", f"Uploaded file: {file.filename}"))
        else:
            user_input = request.form.get('user_input', '').strip()
        
        if 'user_input' in locals() and user_input:
            chat_history.append(("user", user_input))
            messages = [HumanMessage(content=content) if role == "user" else AIMessage(content=content) for role, content in chat_history]
            conf = {"recursion_limit": 100}
            response = graph.invoke({"messages": messages}, conf)
            updated_msgs = response.get("messages", [])
            ai_response = ""
            for msg in updated_msgs:
                if not isinstance(msg, ToolMessage):
                    ai_response = msg.content
            
            if default_language != "English":
                translated_response = translate_text(ai_response, target_language)
                dual_response = (
                    f"<b>English:</b><br>{ai_response}<br><br>"
                    f"<b>{default_language} Translation:</b><br>{translated_response}<br><br>"
                    f"<i>Would you like this script translated and animated?</i>"
                )
                chat_history.append(("assistant", dual_response))
            else:
                chat_history.append(("assistant", ai_response))

            video_file_path = os.path.join(os.getcwd(), "final_output.mp4")
            video_ready = os.path.exists(video_file_path)

        return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    global chat_history, pdf_path, video_ready, default_language, target_language
    
    if request.method == 'POST':
        new_lang = request.form.get('language_select')
        if new_lang:
            default_language = new_lang
            target_language = language_dict[new_lang]
            write_config_lang_code(target_language)
            flash(f"Language changed to {default_language}")

        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            pdf_path = file_path
            flash(f"File uploaded successfully: {file.filename}")
            chat_history.append(("user", f"Uploaded file: {file.filename}"))
            return redirect(url_for('chat'))
        
        user_input = request.form.get('user_input', '').strip()
        if user_input:
            chat_history.append(("user", user_input))
            messages = [HumanMessage(content=content) if role == "user" else AIMessage(content=content) 
                       for role, content in chat_history]
            
            conf = {"recursion_limit": 100}
            response = graph.invoke({"messages": messages}, conf)
            
            updated_msgs = response.get("messages", [])
            ai_response = ""
            for msg in updated_msgs:
                if not isinstance(msg, ToolMessage):
                    ai_response = msg.content
            
            if default_language != "English":
                translated_response = translate_text(ai_response, target_language)
                dual_response = (
                    f"<b>English:</b><br>{ai_response}<br><br>"
                    f"<b>{default_language} Translation:</b><br>{translated_response}<br><br>"
                    f"<i>Would you like this script translated and animated?</i>"
                )
                chat_history.append(("assistant", dual_response))
            else:
                chat_history.append(("assistant", ai_response))

        video_file_path = os.path.join(os.getcwd(), "final_output.mp4")
        video_ready = os.path.exists(video_file_path)
        
        return redirect(url_for('chat'))
    
    return render_template('chat.html', chat_history=chat_history,
                         default_language=default_language, languages=language_dict,
                         video_ready=video_ready)

@app.route('/video/<path:filename>')
def video(filename):
    return send_from_directory(app.config['VIDEO_FOLDER'], filename)

@app.route('/clear', methods=['POST'])
def clear():
    global chat_history, pdf_path, video_ready
    chat_history = []
    pdf_path = ""
    video_ready = False
    return redirect(url_for('chat'))

if __name__ == '__main__':
    app.run(debug=True)