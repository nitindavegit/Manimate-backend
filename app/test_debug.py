#!/usr/bin/env python3
"""
Debug script to test Manim rendering without the API
"""
import sys
import os
sys.path.append('/app')

from .manim_runner import run_manim

# Test code from your logs
test_code = '''from manim import *

class GeneratedScene(Scene):
    def construct(self):
        server = Rectangle(width=2, height=1).shift(LEFT*4)
        client1 = Rectangle(width=2, height=1).shift(RIGHT*4 + UP*2)
        client2 = Rectangle(width=2, height=1).shift(RIGHT*4)
        client3 = Rectangle(width=2, height=1).shift(RIGHT*4 + DOWN*2)
        
        server_label = Text("Server").next_to(server, DOWN)
        client1_label = Text("Client 1").next_to(client1, UP)
        client2_label = Text("Client 2").next_to(client2, RIGHT)
        client3_label = Text("Client 3").next_to(client3, DOWN)
        
        self.add(server, client1, client2, client3)
        self.add(server_label, client1_label, client2_label, client3_label)
        
        arrows = [
            Arrow(server.get_right(), client1.get_left()),
            Arrow(client1.get_left(), server.get_right()),
            Arrow(server.get_right(), client2.get_left()),
            Arrow(client2.get_left(), server.get_right()),
            Arrow(server.get_right(), client3.get_left()),
            Arrow(client3.get_left(), server.get_right()),
        ]
        
        for arrow in arrows:
            self.add(arrow)
        
        self.wait()
'''

if __name__ == "__main__":
    print("🧪 Testing Manim rendering...")
    try:
        result = run_manim(test_code, "GeneratedScene")
        print(f"✅ Success! Generated: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()