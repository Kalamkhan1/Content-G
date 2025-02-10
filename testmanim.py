from manim import *

class PythagoreanTheorem(Scene):
    def construct(self):
        a = 3
        b = 4
        c = (a**2 + b**2) ** 0.5  

        A = np.array([0, 0, 0])
        B = np.array([a, 0, 0])
        C = np.array([0, b, 0])

        triangle = Polygon(A, B, C, color=WHITE, fill_opacity=0.5)
        self.play(Create(triangle), run_time=2)
        self.wait(1)

        square_a = Square(side_length=a, color=BLUE, fill_opacity=0.5).move_to(B + np.array([0, a/2, 0])).rotate(90 * DEGREES)
        square_b = Square(side_length=b, color=GREEN, fill_opacity=0.5).move_to(C + np.array([-b/2, 0, 0]))
        square_c = Square(side_length=c, color=YELLOW, fill_opacity=0.5).move_to(A + B + np.array([-a/2, b/2, 0]))

        self.play(FadeIn(square_a), FadeIn(square_b), FadeIn(square_c), run_time=2)
        self.wait(1)

        square_a_copy = square_a.copy()
        square_b_copy = square_b.copy()

        self.play(
            square_a_copy.animate.rotate(-90 * DEGREES).move_to(square_c.get_center() + np.array([c/4, -c/4, 0])),
            run_time=2
        )
        self.wait(0.5)

        self.play(
            square_b_copy.animate.rotate(90 * DEGREES).move_to(square_c.get_center() + np.array([-c/4, c/4, 0])),
            run_time=2
        )
        self.wait(1)

        self.play(FadeOut(square_a_copy, square_b_copy, triangle, square_a, square_b), run_time=2)

        equation = MathTex("a^2 + b^2 = c^2").move_to(ORIGIN)
        self.play(Write(equation), run_time=2)
        self.wait(1)

        self.play(FadeOut(equation), run_time=2)
