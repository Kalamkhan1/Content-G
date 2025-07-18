import os

from langchain.tools import tool
from translatepy import Translator
from gtts import gTTS
import requests
import time
from utils import get_audio_length,split_script,ANIMATION,run_manim_code,extract_last_error_block
from moviepy import concatenate_videoclips, VideoFileClip,concatenate_audioclips,AudioFileClip,AudioClip
from moviepy.video.fx.Freeze import Freeze
import google.generativeai as genai
import requests
from duckduckgo_search import DDGS

import requests
from duckduckgo_search import DDGS
import time

def search_and_download_image(query, retries=3, delay=1):
    """    
    Search for an image online using DuckDuckGo and download the first result.
    Retries the download up to `retries` times if it fails.

    Returns:
        str or None: 
            - The `save_path` if the image was successfully downloaded.
            - `None` if no images were found or all download attempts failed.
    """
    attempt = 0
    save_path = query + ".jpg"

    while attempt < retries:
        try:
            print(f"Attempt {attempt + 1} of {retries}...")

            # Step 1: Search for images
            with DDGS() as ddgs:
                search_results = list(ddgs.images(query, max_results=1))

            if not search_results:
                print("No images found.")
                return None

            # Step 2: Get the first image URL
            first_image_url = search_results[0]["image"]
            print(f"Image found: {first_image_url}")

            # Step 3: Download the image
            response = requests.get(first_image_url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(save_path, "wb") as file:
                    for chunk in response.iter_content(1024):
                        file.write(chunk)
                print(f"Image successfully downloaded as '{save_path}'")
                return save_path
            else:
                print(f"Download failed with status code {response.status_code}")

        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")

        attempt += 1
        print("Retrying...\n")
        time.sleep(delay)  # Optional delay between retries

    print("All attempts failed. Image could not be downloaded.")
    return None

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

        with open("config.txt", "r") as file:
            target_language=file.read()
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
        print("yayyyyy")
        # if 'image' in point and point['image']:
        #     print("yayyyyy")
        #     image = search_and_download_image(point["image"])
        # else:
        #     image = ''

        print("yaaaaa2")
        # 2. Generate the Manim code prompt and create the video.
        prompt = f"""

        {ANIMATION}

        {point['content']}
        audio length: {audio_len} seconds

        Maintain correctness while taking note of these errors:
        """
        good=False
        it=0

        with open("examples.txt", "r") as file:
            examples = file.read()
        genai.configure(api_key="AIzaSyDScMch20fbg4_DzflmITjyoXarFyMabXg")
        manim_model = genai.GenerativeModel('gemini-2.0-flash')
        chat = manim_model.start_chat()
        response = chat.send_message(examples)
        while not good and it<4:
            it+=1
            print(it,"YYyAAAAAAAAAAAAAAAAYYY")
            response = chat.send_message(prompt, generation_config={"temperature": 0.3})
            response = response.text
            print(response)
            
            # Run the generated Manim code, saving the output to a unique filename.
            output_video_filename = os.path.join(os.getcwd(), f"point_video_{idx}.mp4")
            video_result = run_manim_code(str(response),output_file=output_video_filename)
            if "Error" not in video_result:
                good=True
            print(video_result)
            error_text = extract_last_error_block(video_result)
            prompt = "\n\t\t Got Error:\n\t\t" + error_text + "\n\t\tGive Corrected code in the proper format."
            print(error_text)

            
        if it==4:
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

    # prompt = f"""
    # You will be provided a script point or a Title for a video. I want to you to create Visual Style points for the video that will be created for that script point or title.

    # Example Output Format:
    # Visual Style:
    # -A water drop animates down a curved terrain, dynamically flowing along the surface—no overlays, just natural movement for 15 seconds.
    # -A flat grid appears with two points and a rubber band snapping between them. The grid warps, introducing curvature, and the band follows a new, curved line.
    # -A rotating sphere appears. Highlight the equator in red, then animate multiple curved lines from point to point to depict various geodesics.
    # -Small arrows (vectors) are shown being transported along a curved path on the sphere, staying aligned using parallel transport logic.
    # -Particles travel on complex surfaces—hyperboloids, saddle shapes—tracing geodesics. Overlay faint fields indicating curvature affecting motion till 45 seconds.
    # Note: Not more than 6 points in visual style
    # For the below script point or Title, Write Visual Style
    # {point}
    # """

    # print("yayaya1212")
    # genai.configure(api_key="AIzaSyDScMch20fbg4_DzflmITjyoXarFyMabXg")
    # manim_model = genai.GenerativeModel('gemini-2.0-flash')
    # chat = manim_model.start_chat()
    # response = chat.send_message(prompt, generation_config={"temperature": 0.2})
    # response = response.text