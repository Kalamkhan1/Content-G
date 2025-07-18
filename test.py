from manim import *

class SymmetryInGraphTheory(Scene):
    def construct(self):
        # Set up the graph
        vertices = [Dot(ORIGIN), Dot(LEFT), Dot(RIGHT), Dot(UP), Dot(DOWN)]
        edges = [Line(vertices[0].get_center(), vertices[1].get_center()),
                 Line(vertices[1].get_center(), vertices[2].get_center()),
                 Line(vertices[2].get_center(), vertices[3].get_center()),
                 Line(vertices[3].get_center(), vertices[4].get_center()),
                 Line(vertices[4].get_center(), vertices[0].get_center())]
        graph = VGroup(*vertices, *edges)
        graph.set_color(BLACK)
        graph.scale(0.5)
        self.play(FadeIn(graph))

        # Apply automorphisms
        automorphisms = [
            lambda x: x[::-1],
            lambda x: [x[3], x[1], x[2], x[0], x[4]],
            lambda x: [x[4], x[2], x[3], x[1], x[0]],
            lambda x: [x[0], x[4], x[3], x[2], x[1]],
        ]

        for i, automorphism in enumerate(automorphisms):
            new_vertices = [vertices[automorphism(j)].copy() for j in range(len(vertices))]      
            new_graph = VGroup(*new_vertices, *edges)
            new_graph.set_color(BLACK)
            new_graph.scale(0.5)
            self.play(Transform(graph, new_graph), run_time=1)
            graph = new_graph

            # Color-code vertices based on their new positions
            for j, vertex in enumerate(graph):
                vertex.set_color(HSV(i/len(automorphisms), 1, 1))

        self.wait()