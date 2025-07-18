
from typing import Optional
from pydub.utils import mediainfo
import re
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
from utils import audio_file,video_file,output_file
import subprocess
import tempfile
import os
from translatepy import Translator
from typing import List, Dict, Any

def merge_audio_video():
    """
    Merges an audio file and a video file, limiting the output to the length of the shorter file.

    Args:
        audio_file (str): Path to the audio file (e.g., "a_output.mp3").
        video_file (str): Path to the video file (e.g., "output.mp4").
        output_file (str): Path to save the merged output (e.g., "merged_output.mp4").

    """

    try:
        # Load the audio and video clips
        audio_clip = AudioFileClip(audio_file)
        video_clip = VideoFileClip(video_file)
        
        # Get the durations
        audio_duration = audio_clip.duration
        video_duration = video_clip.duration
        
        # Determine the shorter duration
        final_duration = min(audio_duration, video_duration)

        # Trim the video to the shorter duration
        trimmed_video =  video_clip.subclipped(0, final_duration)

        
        # Trim or adjust the audio to the shorter duration
        trimmed_audio = audio_clip.subclipped(0,final_duration)
        
        # Set the trimmed audio to the video
        final_video = trimmed_video.with_audio(trimmed_audio)
        
        # Export the merged video
        final_video.write_videofile(output_file)
        print(f"Merged file saved as: {output_file}")
    except Exception as e:
        print(f"Error merging files: {e}")



def get_video_length(filename: str) -> Optional[float]:
    """
    Returns the duration of the video file in seconds.
    """
    try:
        # Load the video file using moviepy
        video_clip = VideoFileClip(filename)
        duration = video_clip.duration  # Duration in seconds
        video_clip.close()
        return duration
    except Exception as e:
        print(f"Error while retrieving video length: {e}")
        return None

import re
from typing import List, Dict, Any

def split_script(script: str) -> List[Dict[str, Any]]:
    """
    Splits a structured script into points.
    
    Each point is a dictionary with:
      - "content": the text of the point
      - "image": the image name (if an 'Image:' directive is present)

    Supports both cases where 'Image:' is on a separate line or inline in the paragraph.
    """
    paragraphs = re.split(r'\n\s*\n+', script.strip())
    points: List[Dict[str, Any]] = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Try to find "Image: ..." anywhere in the paragraph
        image_match = re.search(r'\bImage:\s*([^\n]+)', para)
        image_name = image_match.group(1).strip() if image_match else None

        # Remove the 'Image: ...' part from the content
        if image_match:
            para = para[:image_match.start()].strip()

        point: Dict[str, Any] = {"content": para}
        if image_name:
            point["image"] = image_name

        points.append(point)

    return points


def get_audio_length(filename):
    """
    Returns the duration of the audio file in seconds.
    """
    try:
        # Use pydub's mediainfo to get the duration of the audio file
        audio_info = mediainfo(filename)
        return float(audio_info['duration'])
    except Exception as e:
        print(f"Error while retrieving audio length: {e}")
        return None
    

def extract_manim_code(response: str) -> str:
    """
    Extracts Manim code from the given response starting with 'from manim import *'.
    
    Args:
        response (str): The raw response string containing the Manim code.
    
    Returns:
        str: The extracted Manim code, or an error message if no code is found.
    """
    # Regular expression to extract code starting from 'from manim import *'
    match = re.search(r"(from manim import \*.*?```)", response, re.DOTALL)
    if match:
        # Clean up the extracted code by removing leading/trailing artifacts
        code = match.group(1)
        code = code.replace("```python\n", "").replace("```", "").strip()
        return code
    else:
        return "Error: Manim code not found in the response."




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



def translate(script:str,target_language:str) -> str:
    translator = Translator()
    translated_result = translator.translate(script, target_language)
    translated_text = translated_result.result  # Get translated text
    return translated_text


def extract_last_error_block(output: str) -> str:
    lines = output.strip().split('\n')
    error_block = []
    found = False

    # Walk backward to find the beginning of the last error
    for line in reversed(lines):
        if not found and line.strip() == "":
            continue  # skip trailing empty lines
        error_block.insert(0, line)
        if any(line.strip().startswith(prefix) for prefix in ["Traceback", "ValueError", "TypeError", "RuntimeError", "Exception"]):
            break

    return "\n".join(error_block).strip()
