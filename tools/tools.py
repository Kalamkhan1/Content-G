import os

from langchain.tools import tool
from translatepy import Translator
from gtts import gTTS
import requests
import time
from utils import get_audio_length,split_script,ANIMATION,run_manim_code
from moviepy import concatenate_videoclips, VideoFileClip,concatenate_audioclips,AudioFileClip,AudioClip
from moviepy.video.fx.Freeze import Freeze
import google.generativeai as genai
import config



  
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
        target_language=config.target_language
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
        print(f"Processing point {idx}")
        
        # 1. Generate audio for the point.
        text_for_tts = f"{point['content']}"
        try:
            translated_text, audio_len = translate_and_text_to_speech(text_for_tts)
        except Exception as e:
            continue
        
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
        {point['content']}
        audio length: {audio_len} seconds

        {ANIMATION}

        Maintain correctness while taking note of these errors:
        """
        good=False
        it=0
        manim_model = genai.GenerativeModel('gemini-1.5-flash-8b-latest')
        chat = manim_model.start_chat()
        while not good and it<6:
            it+=1
            print(it,"YYyAAAAAAAAAAAAAAAAYYY")
            response = chat.send_message(prompt, generation_config={"temperature": 0.2})
            response = response.text
            print(response,"hiiiii!")
            
            # Run the generated Manim code, saving the output to a unique filename.
            output_video_filename = os.path.join(os.getcwd(), f"point_video_{idx}.mp4")
            video_result = run_manim_code(str(response),output_file=output_video_filename)
            if "Error" not in video_result:
                good=True
            print(video_result)
            prompt="\n\t\t Got Error:\n\t\t" + next((line for line in reversed(video_result.split("\n")) if line.strip()), "") + "\n\t\tGive Corrected code in the proper format."
            print(next((line for line in reversed(video_result.split("\n")) if line.strip()), ""))
            
        if it==6:
            continue
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
