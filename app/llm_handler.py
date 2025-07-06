from openai import OpenAI
from app.config import OPENAI_API_KEY, OPENAI_BASE_URL
import os
import re

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

def get_manim_code(prompt: str) -> str:
    system_prompt = (
        "You are a Manim expert. Your sole task is to generate valid Python code using the Manim library to visualize the prompt provided by the user. "
        "The code must be complete and self-contained, importing all necessary modules. "
        "Always name the scene class as 'GeneratedScene' and it must inherit from Scene. "
        "Never include any explanation, comment, markdown formatting, or natural language of any kind. "
        "Do not include triple quotes, code block markers (like ```), or any descriptive text before or after the code. "
        "Only return plain Python code—no extra whitespace, comments, or instructions of any kind. "
        "Output must start directly with the 'from manim import *' line. "
        "The construct() method must be properly defined with correct indentation. "
        "Make sure all code is properly indented and syntactically correct."
        "Ensure that all text and visual elements are spaced out so that nothing overlaps. Use appropriate positioning and buffer values to keep all labels and arrows readable and separated. "
        "Ensure self.wait() is included at the end of the construct() method. "
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        raw = response.choices[0].message.content.strip()
        
        # Clean up the response - handle various markdown formats
        if "```" in raw:
            # Remove code block markers
            raw = raw.replace("```python", "").replace("```", "").strip()
        
        # Remove any remaining backticks and extra whitespace
        raw = raw.strip("`").strip()
        
        # Remove any leading/trailing markdown or explanations
        lines = raw.split('\n')
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('from manim import'):
                start_idx = i
                break
        
        if start_idx > 0:
            raw = '\n'.join(lines[start_idx:])
        
        # Ensure proper structure
        if not raw.startswith("from manim import"):
            if "from manim import" in raw:
                # Find the start of the actual code
                start_idx = raw.find("from manim import")
                raw = raw[start_idx:]
            else:
                # Add the import if missing
                raw = "from manim import *\n\n" + raw
        
        # Check if GeneratedScene class exists
        if "class GeneratedScene" not in raw:
            raise Exception("Generated code must contain a 'GeneratedScene' class")
        
        # Ensure self.wait() is present
        if "self.wait()" not in raw:
            # Try to add it before the last line of the construct method
            lines = raw.split('\n')
            # Find the construct method and add self.wait() before its end
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith(' ') and not line.startswith('\t') and i > 0:
                    # This might be the end of the construct method
                    if i < len(lines) - 1:
                        lines.insert(i, "        self.wait()")
                        break
            else:
                # If we can't find a good spot, add it at the end
                raw += "\n        self.wait()"
            raw = '\n'.join(lines)
        
        return raw
        
    except Exception as e:
        print(f"Error generating Manim code: {e}")
        # Return a simple fallback scene
        return """from manim import *

class GeneratedScene(Scene):
    def construct(self):
        text = Text("Error generating animation")
        self.play(Write(text))
        self.wait()"""