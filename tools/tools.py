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
from utils import get_audio_length,get_video_length,target_language,split_script,ANIMATION
from moviepy import concatenate_videoclips, VideoFileClip,concatenate_audioclips,AudioFileClip,AudioClip
from moviepy.video.fx.Freeze import Freeze
import google.generativeai as genai



def run_manim_code(code: str, output_file: Optional[str] = "output.mp4") -> str:
    """
    Runs the specified Manim code, generates animations for all Scene classes,
    combines them into one video, and saves the final output in the current directory.
    After generating the video, calculates and prints its duration.
    """
    pattern = r"```python\s*(.*?)```"
    match = re.search(pattern, code, re.DOTALL)
    if match:
        # Return the captured group with any leading/trailing whitespace removed.
        code= match.group(1).strip()

    # Delete the output file if it already exists
    if os.path.exists(output_file):
        print(f"Output file '{output_file}' already exists. Deleting it...")
        os.remove(output_file)

    # Extract all Scene classes
    scene_classes = re.findall(r"class\s+(\w+)\(Scene\):", code)
    if not scene_classes:
        return "Error: Manim code must contain at least one class inheriting from Scene."

    # Use a temporary directory for execution
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, "temp_manim_script.py")
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        try:
            # Save the Manim code to a temporary file
            with open(temp_file_path, "w", encoding="utf-8") as file:
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
            # Combine all video clips into one
            final_video_path = os.path.join(os.getcwd(), output_file)
            if len(video_clips)>1:
                final_video = concatenate_videoclips(video_clips)    
            else :
                final_video = video_clips[0]
            final_video.write_videofile(final_video_path)
            final_video.close()
            # Calculate and return the video length
            video_length = get_video_length(final_video_path)
            if video_length is not None:
                print(f"Final video duration: {video_length:.2f} seconds")

            return f"Combined animation generated."

        except Exception as e:
            print(f"Error: {str(e)}")
            return f"Error: {str(e)}"




  
@tool
def translate_and_text_to_speech(script:str) -> str:
    """
    Translates the given script to the target language, converts it into speech, and saves it as an audio file.
    Retries the TTS operation up to retries times if it fails due to network issues.
    """
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

                return translated_text,audio_length
                
            except requests.exceptions.RequestException as e:
                if attempt < retries - 1:
                    time.sleep(2)  # Wait before retrying
                else:
                    return "Failed to generate audio after multiple attempts."

    except Exception as e:
        return f"An error occurred during translation or TTS: {e}"






@tool
def create_script_animate(script: str) -> str:
    """
    Processes the given script by:
      1. Splitting it into individual points.
      2. For each point:
         - Generating TTS audio.
         - Generating a Manim video.
         - Merging the point's audio and video by extending the shorter of the two 
           to match the duration of the longer.
      3. Finally, concatenating all the merged point videos (each with audio) into one final video.
    """
    # Split the script into individual points.
    points = split_script(script)

    merged_point_videos = []  # These will store the per-point merged video files

    for idx, point in enumerate(points):
        print(f"Processing point {idx}: {point['title']}")
        
        # 1. Generate audio for the point.
        text_for_tts = f"{point['title']}\n{point['content']}"
        try:
            translated_text, audio_len = translate_and_text_to_speech(text_for_tts)
        except Exception as e:
            return f"Error during TTS for point {idx}: {e}"
        
        src_audio = os.path.join(os.getcwd(), "a_output.mp3")
        target_audio = os.path.join(os.getcwd(), f"audio_point_{idx}.mp3")
        try:
            if os.path.exists(target_audio):
                print(f"Output file '{target_audio}' already exists. Deleting it...")
                os.remove(target_audio)
            os.rename(src_audio, target_audio)
        except Exception as e:
            return f"Error renaming audio file for point {idx}: {e}"

        # 2. Generate the Manim code prompt and create the video.
        prompt = f"""
        ```
        {point['title']}
        {point['content']}
        ```
        audio length:``` {audio_len}``` seconds
        ```
        {ANIMATION}
        ```
        """
        good=False
        while not good:
            manim_model = genai.GenerativeModel('gemini-1.5-flash-8b-latest')
            response = manim_model.generate_content(prompt, generation_config={"temperature": 0.2})
            response = response.text
            
            # Run the generated Manim code, saving the output to a unique filename.
            output_video_filename = os.path.join(os.getcwd(), f"point_video_{idx}.mp4")
            video_result = run_manim_code(str(response),output_file=output_video_filename)

            if "Error" not in video_result:
                good=True
                
        try:
            video_clip = VideoFileClip(output_video_filename)
            if not hasattr(video_clip, "fps") or video_clip.fps is None:
                print("Nooooooo!!!!!!!!!!!!")
                video_clip = video_clip.with_fps(30)
            audio_clip = AudioFileClip(target_audio)
        except Exception as e:
            return f"Error loading clips for point {idx}: {e}"
        
        # Determine the maximum duration between audio and video.
        max_duration = max(video_clip.duration, audio_len)
        
        # Extend video by freezing the last frame if it's shorter.
        if video_clip.duration < max_duration:
            try:
                
                freeze_effect = Freeze(t=video_clip.duration - 0.001,
                       freeze_duration=(max_duration - video_clip.duration))
                extended_video = freeze_effect.apply(video_clip) 
                
                extended_audio=audio_clip
            except Exception as e:
                return f"Error freezing video for point {idx}: {e}"
        else:
            try:
                silence_duration = max_duration - audio_len
                
                silence_audio = AudioClip(lambda t: 0, duration=silence_duration, fps=audio_clip.fps)
                extended_audio = concatenate_audioclips([audio_clip, silence_audio])
                extended_video=video_clip
            except Exception as e:
                return f"Error extending audio for point {idx}: {e}"
        # Set the extended audio to the extended video.
        merged_clip = extended_video.with_audio(extended_audio)
        folder_path = os.path.join(os.getcwd(), f"points")
        os.makedirs(folder_path, exist_ok=True)
        merged_output_filename = os.path.join(folder_path, f"merged_point_{idx}.mp4")
        if os.path.exists(merged_output_filename):
            print(f"Output file '{merged_output_filename}' already exists. Deleting it...")
            os.remove(merged_output_filename)
        try:
            merged_clip.write_videofile(merged_output_filename)
        except Exception as e: 
            return f"Error writing merged video for point {idx}: {e}"
        merged_point_videos.append(merged_output_filename)

        video_clip.close()
        audio_clip.close()
        extended_video.close()
        extended_audio.close()
        merged_clip.close()
        if os.path.exists(output_video_filename):
            print(f"Output file '{output_video_filename}' already exists. Deleting it...")
            os.remove(output_video_filename)
        if os.path.exists(target_audio):
            print(f"Output file '{target_audio}' already exists. Deleting it...")
            os.remove(target_audio)

    try:
        final_clips = [VideoFileClip(v) for v in merged_point_videos]
        final_video_clip = concatenate_videoclips(final_clips)
        final_output_file = os.path.join(os.getcwd(), "final_output.mp4")
        final_video_clip.write_videofile(final_output_file)
        # Close all clips.
        for clip in final_clips:
            clip.close()
        final_video_clip.close()
    except Exception as e:
        return f"Error merging final videos: {e}"
    
    return f"Final video generated: {final_output_file}"
