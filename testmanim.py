from manim import *
import numpy as np

class PolarDemo(Scene):
    def construct(self):
        def polarf(theta):
            return 2 - 2 * np.sin(theta)

        self.camera.background_color = WHITE
        tempo = 1.5
        axes = PolarPlane(radius_max=4).add_coordinates()
        table = MathTable([[r"\theta", r"r=2-2\sin\theta"],
                           [0, 2], [r"\pi/6", 1], [r"\pi/2", 0], [r"\pi", 2], [r"3\pi/2", 4]]).scale(0.7)
        layout = VGroup(axes, table).arrange(RIGHT, buff=LARGE_BUFF)

        self.play(DrawBorderThenFill(axes), FadeIn(table), run_time=3 * tempo)
        tvals = [0, PI / 6, PI / 2, PI, 3 * PI / 2]
        colors = [BLUE, GREEN, RED, ORANGE, PURPLE]
        
        for tval, color in zip(tvals, colors):
            r = polarf(tval)
            vec = Arrow(start=axes.polar_to_point(0, 0),
                        end=axes.polar_to_point(r, tval),
                        color=color, buff=0)
            dot = Dot(axes.polar_to_point(r, tval), color=color)
            self.play(Create(vec), run_time=tempo)
            self.play(FadeIn(dot), FadeOut(vec), run_time=tempo)
        
        t = ValueTracker(0)
        dot = always_redraw(lambda: Dot(axes.polar_to_point(polarf(t.get_value()), t.get_value()), color=RED))
        curve = always_redraw(lambda: ParametricFunction(lambda u: axes.polar_to_point(polarf(u), u),
                                                          t_range=[0, t.get_value()], color=RED, stroke_width=6))
        self.play(FadeIn(dot, curve), run_time=tempo)
        self.play(t.animate.set_value(2 * PI), run_time=6 * tempo)
        self.play(FadeOut(dot, curve, table, axes), run_time=2 * tempo)