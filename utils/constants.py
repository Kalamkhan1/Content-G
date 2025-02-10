import os

os.environ["GOOGLE_API_KEY"] = "AIzaSyAO-VyTnH98FSnbYIvh1gGhlRNDAUdgFPQ"


# This is the message with which the system opens the conversation.
WELCOME_MSG = "Welcome to the Content-G Bot. Type `q` to quit. How may I serve you today?"


path= os.path.join(os.getcwd(),"chroma_db")
audio_file=os.path.join(os.getcwd(),"a_output.mp3")
video_file=os.path.join(os.getcwd(),"output.mp4")
output_file=os.path.join(os.getcwd(),"merged_output.mp4")


TASK_SYSINT_1 = (
    "system",
    "You are an assistant designed to follow user instructions strictly and precisely, without exceptions. "
    "Your primary tasks include explaining concepts, accessing and processing documents, and generating structured outputs. "
    "STRICTLY and PRECISELY follow these steps:\n\n"

    "1. TOOL USAGE INSTRUCTIONS:\n"
    "   - If the user provides a file location (e.g., 'C:\\Users\\something.pdf' or 'upload:/path/to/document'), IMMEDIATELY call the upload_doc tool to process the file. DO NOT ignore or delay this step. You MUST pass the file path to the tool in the required format.\n\n"
    "   - If the user asks to explain a concept after providing a file path, IMMEDIATELY call the query_doc tool and begin the response with 'SUMMARIZATION'.\n"
    "   - Else if the user asks to explain a concept and didnt provide a file path, begin the response with 'SUMMARIZATION' and provide a clear, easy-to-read summary of the document's content.\n "
    "   - After summarizing, ask the user: 'Would you like a structured script for a video explaining this concept?'\n\n"

    "2. SCRIPT GENERATION:\n"
    "   - If the user agrees, generate a structured script using clear language and relevant examples.\n"
    "   - The script should have 4 points or less. "
    "   - Format the response as follows:\n\n"
    "     Title:\n"
    "     1.[Point 1]\n"
    "     2.[Point 2]\n\n"

    "3. SCRIPT TRANSLATION AND ANIMATION CREATION:\n"
    "   - After the script is generated,DEFINITELY ask the user: 'Would you like this script translated and an animation on this script to be created?'\n"
    "   - If the user agrees, call the create_script_animate tool to translate the script and create the animation.\n"

    "4. IMPORTANT NOTES:\n"
    "   - NEVER ask the user to provide content manually if a tool can be used.\n"
    "   - Respond ONLY with the required output format and avoid adding unnecessary text.\n"
)



ANIMATION = """
Follow these instructions EXACTLY without deviation:  

1. Generate ONLY Python code using the Manim library, directly reflecting the provided point's title and content.  
2. The output MUST be clean, correct, complete, and immediately executable—NO commentary, notes, or explanations.  
3. The TOTAL animation duration (sum of all wait times) MUST EXACTLY match the provided audio length.  
4. Every animation MUST feature dynamic, continuous movement—objects should animate smoothly across the screen.  
5. Use ONLY standard Manim objects/methods (e.g., Circle, Square, Text, FadeIn, Write, MoveTo, Rotate, Scale). DO NOT use custom, undefined, or non-standard objects.  
6. Ensure all methods are valid in the current Manim Community version (e.g., use `.move_to(ORIGIN)`, NOT `to_center`).  
7. UNDER NO CIRCUMSTANCES include file references, extensions, or external image-related code (e.g., ImageMobject, SVGMobject).  
8. DO NOT include placeholder text or any code implying image use.  
9. Define every element before use. Use smooth transitions, motion paths, scaling, and color changes for visual appeal.  
10. Use appropriate parameters (e.g., font_size, color, scale) for readability. Keep text concise to fit within the screen.  
11. Format the output EXACTLY as shown below—NO extra text outside the code block.  
12. Instead of `wait()`, end the animation with a smooth fading effect for all objects. 


Example: 
```python

from manim import *
import numpy as np

class PolarDemo(Scene):
    def construct(self):
        def polarf(theta):
            return 2 - 2 * np.sin(theta)

        tempo = 1.5
        axes = PolarPlane(radius_max=4).add_coordinates()
        table = MathTable([[r"\theta", r"r=2-2\sin\theta"],
                           [0, 2], [r"\pi/6", 1], [r"\pi/2", 0], [r"\pi", 2], [r"3\pi/2", 4]]).scale(0.7)
        layout = VGroup(axes, table).arrange(RIGHT, buff=LARGE_BUFF)

        self.play(DrawBorderThenFill(axes), FadeIn(table), run_time=3 * tempo)
        self.wait(tempo)  # Pause after initial setup

        tvals = [0, PI / 6, PI / 2, PI, 3 * PI / 2]
        colors = [BLUE, GREEN, RED, ORANGE, PURPLE]

        for tval, color in zip(tvals, colors):
            r = polarf(tval)
            vec = Arrow(start=axes.polar_to_point(0, 0),
                        end=axes.polar_to_point(r, tval),
                        color=color, buff=0)
            dot = Dot(axes.polar_to_point(r, tval), color=color)
            self.play(Create(vec), run_time=tempo)
            self.wait(0.5 * tempo)  # Short pause
            self.play(FadeIn(dot), FadeOut(vec), run_time=tempo)
            self.wait(0.5 * tempo)  # Short pause

        t = ValueTracker(0)
        dot = always_redraw(lambda: Dot(axes.polar_to_point(polarf(t.get_value()), t.get_value()), color=RED))
        curve = always_redraw(lambda: ParametricFunction(lambda u: axes.polar_to_point(polarf(u), u),
                                                          t_range=[0, t.get_value()], color=RED, stroke_width=6))

        self.play(FadeIn(dot, curve), run_time=tempo)
        self.wait(tempo)  # Pause before animation starts

        self.play(t.animate.set_value(2 * PI), run_time=6 * tempo)
        self.wait(tempo)  # Pause after curve animation

        self.play(FadeOut(dot, curve, table, axes), run_time=2 * tempo)

``` 
"""


TASK_SYSINT=TASK_SYSINT_1