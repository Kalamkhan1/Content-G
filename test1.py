import streamlit as st
from models import llm_with_tools
from tools import run_manim_code, translate_and_text_to_speech
from utils import merge_audio_video
import os

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []  # To store conversation
if 'step' not in st.session_state:
    st.session_state.step = 1  # To track the flow
if 'explanation' not in st.session_state:
    st.session_state.explanation = ""

# Helper functions
def handle_explanation(user_input):
    """Generate an explanation from the LLM."""
    try:
        response = llm_with_tools.invoke(user_input)
        return response.content
    except Exception as e:
        return f"Error: {str(e)}"

def generate_video_and_audio(script_text):
    """Generate video and audio narration for the script."""
    try:
        # Escape any special characters like quotes or newlines
        script_text = script_text.replace('"', '\\"').replace("'", "\\'").replace('\n', '\\n')

        # Get Manim code from the model (use the LLM for dynamic code generation)
        manim_code = llm_with_tools.invoke(f"Generate Manim code for the following explanation: {script_text}")
        
        print(f"Generated Manim code: {manim_code.additional_kwargs['function_call']['arguments']['code']}")

        # Pass the generated Manim code to Manim
        video_path = run_manim_code(manim_code)
        
        # Generate the corresponding audio
        audio_path = translate_and_text_to_speech(script_text)
        
        return video_path, audio_path
    except Exception as e:
        return None, f"Error: {str(e)}"

# Main app function
def main():
    st.set_page_config(page_title="Content-G Modular", page_icon="🤖", layout="centered")
    st.title("🤖 Content-G Modular Assistant")

    # Display conversation
    for msg in st.session_state.messages:
        role = "You" if msg["role"] == "user" else "AI"
        st.markdown(f"**{role}:** {msg['content']}")

    # Step 1: Input prompt or upload file
    if st.session_state.step == 1:
        st.markdown("### Enter a prompt or upload a document to get started:")
        user_input = st.text_input("Enter your prompt or question:")
        uploaded_file = st.file_uploader("Upload a PDF:", type=["pdf"])

        if st.button("Submit"):
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                explanation = handle_explanation(user_input)
                st.session_state.messages.append({"role": "ai", "content": explanation})
                st.session_state.explanation = explanation
                st.session_state.step = 2
            elif uploaded_file:
                st.session_state.messages.append({"role": "user", "content": "Uploaded a document."})
                explanation = "Extracted text from the uploaded document (placeholder)."
                st.session_state.messages.append({"role": "ai", "content": explanation})
                st.session_state.explanation = explanation
                st.session_state.step = 2
            else:
                st.warning("Please enter a prompt or upload a document.")

    # Step 2: Ask user if they want a video/audio explanation
    elif st.session_state.step == 2:
        st.markdown("### Would you like an animated explanation with audio?")
        if st.button("Yes, generate animation"):
            st.session_state.step = 3
        elif st.button("No, that's all"):
            st.session_state.messages.append({"role": "ai", "content": "Let me know if you need anything else!"})
            st.session_state.step = 1

    # Step 3: Generate video and audio
    elif st.session_state.step == 3:
        st.write("Generating video and audio... Please wait.")
        explanation = st.session_state.explanation
        
        video_path, audio_or_error = generate_video_and_audio(explanation)
        audio_or_error=r"C:\Users\kalam\Desktop\Content-G\Content-G-M\a_output.mp3"
        video_path=r"C:\Users\kalam\Desktop\Content-G\Content-G-M\output.mp4"

        print("path finding")
        print(video_path)
        
        # Check if video file exists before displaying
        if os.path.exists(video_path):
            st.session_state.messages.append({"role": "ai", "content": "Here's your animated explanation:"})
            st.video(video_path)
            st.audio(audio_or_error)  # Audio path
            print("path found")
        else:
            st.session_state.messages.append({"role": "ai", "content": f"An error occurred: {audio_or_error}"})

        st.session_state.step = 1

    # Sidebar for instructions
    st.sidebar.info(
        """
        **How to Use**:
        1. Enter a concept or upload a document.
        2. Get a text explanation from the AI.
        3. Optionally, generate an animated video with audio narration.
        """
    )

if __name__ == "__main__":
    main()
