import os
import re
import subprocess
import tempfile
from typing import Optional
from langchain.tools import tool
from translatepy import Translator
from gtts import gTTS
import requests
import time
from utils import get_audio_length,get_video_length
from moviepy import concatenate_videoclips, VideoFileClip

def run_manim_code(code: str, output_file: Optional[str] = "output.mp4") -> str:
    """
    Runs the specified Manim code, generates animations for all Scene classes,
    combines them into one video, and saves the final output in the current directory.
    After generating the video, calculates and prints its duration.
    """

    print("Received Manim Code:")
    print(code)

    # Extract all Scene classes
    scene_classes = re.findall(r"class\s+(\w+)\(Scene\):", code)
    if not scene_classes:
        return "Error: Manim code must contain at least one class inheriting from Scene."
    print("Detected Scene Classes:", scene_classes)

    # Use a temporary directory for execution
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, "temp_manim_script.py")
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        try:
            # Save the Manim code to a temporary file
            with open(temp_file_path, "w") as file:
                file.write(code)

            # Check if Manim is installed and accessible
            manim_check = subprocess.run(
                ["manim", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if manim_check.returncode != 0:
                return f"Error: Manim is not installed or not accessible.\n{manim_check.stderr}"

            # Render each Scene class separately
            video_clips = []
            for scene_class in scene_classes:
                result = subprocess.run(
                    ["manim", temp_file_path, scene_class, "-ql", "--media_dir", output_dir],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                if result.returncode != 0:
                    return f"Error while generating animation for {scene_class}:\n{result.stderr}"

                # Locate the generated video file
                generated_video_path = None
                for root, _, files in os.walk(output_dir):
                    for file in files:
                        if file.endswith(".mp4") and scene_class in file:
                            generated_video_path = os.path.join(root, file)
                            break
                    if generated_video_path:
                        break

                if not generated_video_path:
                    return f"Error: Animation for {scene_class} generated but output file not found."

                # Load the video into MoviePy for combining
                video_clips.append(VideoFileClip(generated_video_path))

            # Combine all video clips into one
            final_video = concatenate_videoclips(video_clips)
            final_video_path = os.path.join(os.getcwd(), output_file)
            final_video.write_videofile(final_video_path)

            # Calculate and return the video length
            video_length = get_video_length(final_video_path)
            if video_length is not None:
                print(f"Final video duration: {video_length:.2f} seconds")

            return f"Combined animation generated and saved as '{output_file}'."

        except Exception as e:
            return f"Error: {str(e)}"

  
@tool
def translate_and_text_to_speech(script:str) -> str:
    """
    Translates the given script to the target language, converts it into speech, and saves it as an audio file.
    Retries the TTS operation up to retries times if it fails due to network issues.
    """
    target_language="ja"
    filename='a_output.mp3'
    retries=3
    try:
        translator = Translator()
        # Translate the text to the target language
        translated_result = translator.translate(script, target_language)
        translated_text = translated_result.result  # Get translated text
        print(f"Translated Text:\n{translated_text}\n")

        # Step 2: Convert the translated text into speech with retries
        for attempt in range(retries):
            try:
                tts = gTTS(text=translated_text, lang=target_language, slow=False)
                
                # Ensure the file is saved in the current directory
                output_path = os.path.join(os.getcwd(), filename)
                tts.save(output_path)

                # Get the audio length
                audio_length = get_audio_length(output_path)
                if audio_length is not None:
                    print(f"Audio Length: {audio_length} seconds")

                return translated_text
                
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    print("Retrying...")
                    time.sleep(2)  # Wait before retrying
                else:
                    return "Failed to generate audio after multiple attempts."

    except Exception as e:
        return f"An error occurred during translation or TTS: {e}"