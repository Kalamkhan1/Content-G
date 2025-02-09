from moviepy import VideoFileClip
from moviepy.video.fx.Freeze import Freeze

def create_and_freeze_video(output_path="output.mp4", freeze_duration=15):
    """
    Loads a video file, applies a freeze effect at the end, and extends the video.
    
    :param output_path: Path to save the final video.
    :param freeze_duration: How long the freeze effect should last.
    """
    
    # Load the existing video
    video = VideoFileClip("input.mp4")

    # Ensure FPS is correctly set (only if it's missing)
    if not hasattr(video, "fps") or video.fps is None:
        video = video.set_fps(30)  # Set default FPS if missing

    print(f"Video FPS: {video.fps}")

    # Apply freeze effect
    freeze_effect = Freeze(t="end", freeze_duration=freeze_duration)
    frozen_clip = freeze_effect.apply(video)

    print("Applying freeze effect...")

    # Save the final output
    frozen_clip.write_videofile(output_path, codec="libx264", fps=video.fps)
    print(f"Final video saved as {output_path}")

# Run the function with a video file
create_and_freeze_video()
