
from typing import Optional
from pydub.utils import mediainfo
import re
from moviepy import VideoFileClip, AudioFileClip
from utils import audio_file,video_file,output_file
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
