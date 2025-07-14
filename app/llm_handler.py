from openai import OpenAI
from openai import RateLimitError
from app.config import OPENAI_API_KEY, OPENAI_BASE_URL
import os
import re

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

def get_manim_code(prompt: str) -> str:
    system_prompt = (
    "You are a Manim Community v0.19.0 expert focused on producing always-valid and runnable Python code.\n\n"

    "## FORMAT & STRUCTURE\n"
    "- Output ONLY valid Python code — absolutely no markdown, comments, or explanations.\n"
    "- First lines MUST be:\n"
    "    from manim import *\n"
    "    import numpy as np\n"
    "- Define exactly ONE class: `GeneratedScene`, inheriting from `Scene` (2D) or `ThreeDScene` (3D).\n"
    "- Must have a `def construct(self):` method, ending with `self.wait(2)`.\n\n"

    "## SUPPORTED ELEMENTS\n"
    "- Text (use `Text(...)`, no `font_size` over 64, ideally between 36–60).\n"
    "- Math: use `MathTex(...)` for equations.\n"
    "- Shapes: `Circle`, `Square`, `Dot`, `Line`, `Arrow`, `Rectangle`, `Polygon`.\n"
    "- Graphs: Use `Axes(...).plot(...)`. Label with `axes.get_graph_label(graph, label=\"...\", x_val=...)`.\n"
    "- NEVER add `font_size` to `get_graph_label()` — this is NOT supported in v0.19.0.\n"
    "- Shade area: `axes.get_area(graph, x_range=[a, b], color=..., opacity=0.5)`.\n\n"

    "## SPATIAL & VISUAL RULES\n"
    "- All elements MUST stay inside the visible frame (~14 units wide).\n"
    "- At the end of construct(), always group all elements with VGroup(*self.mobjects), then scale_to_fit_width(12) and move_to(ORIGIN).\n"
    "- Make sure every text, shape or elements must be inside the visible frame."
    "- Use `.scale_to_fit_width(12)` or `.scale(0.9)` on large VGroups/diagrams."
    "- Prefer `.to_edge(LEFT/RIGHT)` or `.next_to()` for positioning — never let text or objects overflow the screen."
    "- Use `VGroup(...).arrange(RIGHT, buff=1)` to space diagram columns (e.g., layers in a neural network)."
    "- NEVER let text, shapes, or graphs touch or overlap.\n"
    "- Use `.next_to()`, `.shift()`, or `.to_edge()` to position items with spacing.\n"
    "- Stack elements vertically with `DOWN`, `UP`, or use `aligned_edge=...` for layout.\n"
    "- Use `.scale()` if needed to prevent visual collisions.\n"
    "- Always check that large text/equations stay centered or within bounds.\n\n"

    "## 3D SCENE RULES\n"
    "- Use `ThreeDScene` ONLY when needed.\n"
    "- Valid 3D objects: `Surface`, `ThreeDAxes`, `Sphere`, `Cube`, `Cylinder`.\n"
    "- DO NOT use `ParametricSurface` — use `Surface(...)` with `fill_color`, `stroke_color`, etc.\n"
    "- Set camera using: `self.set_camera_orientation(phi=75*DEGREES, theta=30*DEGREES)`.\n"
    "- For movement, use: `self.begin_ambient_camera_rotation(rate=0.2)`.\n\n"

    "## STABILITY & SAFETY\n"
    "- Use only methods and arguments supported in Manim Community v0.19.0.\n"
    "- Avoid deprecated or experimental features.\n"
    "- Ensure animations are smooth using `Write`, `Create`, `FadeIn`, or `Transform`.\n"
    "- NEVER crash — return fallback if concept is too abstract.\n\n"

    "## FALLBACK (if concept is not visualizable)\n"
    "from manim import *\n"
    "import numpy as np\n\n"
    "class GeneratedScene(Scene):\n"
    "    def construct(self):\n"
    "        self.play(Write(Text(\"❌ Visualization not supported\", font_size=36, color=RED)))\n"
    "        self.wait(2)\n\n"

    "## GOAL\n"
    "Generate clear, organized, and educational Manim scenes that ALWAYS render without errors. Ensure visual clarity, spacing, and compatibility with v0.19.0."
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

        if "```" in raw:
            raw = raw.replace("```python", "").replace("```", "").strip()

        raw = raw.strip("`").strip()
        lines = raw.split('\n')
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('from manim import'):
                start_idx = i
                break
        if start_idx > 0:
            raw = '\n'.join(lines[start_idx:])

        if not raw.startswith("from manim import"):
            if "from manim import" in raw:
                start_idx = raw.find("from manim import")
                raw = raw[start_idx:]
            else:
                raw = "from manim import *\nimport numpy as np\n\n" + raw

        lines = raw.split('\n')
        new_lines = []
        imports_added = False

        for line in lines:
            if line.strip().startswith('from manim import') and not imports_added:
                new_lines.append("from manim import *")
                imports_added = True
            elif line.strip().startswith('import numpy as np'):
                new_lines.append(line)
            elif not line.strip().startswith('from manim') and not line.strip().startswith('import manim'):
                new_lines.append(line)

        if not imports_added:
            new_lines.insert(0, "from manim import *")

        if not any("import numpy as np" in line for line in new_lines):
            insert_pos = 1
            for i, line in enumerate(new_lines):
                if line.strip().startswith('from manim import'):
                    insert_pos = i + 1
                    break
            new_lines.insert(insert_pos, "import numpy as np")

        raw = '\n'.join(new_lines)

        needs_3d_scene = any(obj in raw for obj in [
            'Surface', 'ThreeDAxes', 'ThreeDScene', 'Sphere', 'Cube', 'Cylinder', 'Cone', 'Torus', 'set_camera_orientation'
        ])

        if needs_3d_scene:
            if "class GeneratedScene(Scene):" in raw:
                raw = raw.replace("class GeneratedScene(Scene):", "class GeneratedScene(ThreeDScene):")

        if "class GeneratedScene" not in raw:
            raise Exception("Generated code must contain a 'GeneratedScene' class")

        if "self.wait(" not in raw:
            lines = raw.split('\n')
            construct_indent = None
            last_construct_line = -1

            for i, line in enumerate(lines):
                if "def construct(self):" in line:
                    construct_indent = len(line) - len(line.lstrip())
                elif construct_indent is not None and line.strip():
                    if len(line) - len(line.lstrip()) > construct_indent:
                        last_construct_line = i
                    elif len(line) - len(line.lstrip()) <= construct_indent:
                        break

            if last_construct_line >= 0:
                indent = ' ' * (construct_indent + 4)
                lines.insert(last_construct_line + 1, f"{indent}self.wait(2)")
            else:
                lines.append("        self.wait(2)")

            raw = '\n'.join(lines)

        return raw

    except RateLimitError as e:
        print("🚫 OpenAI API quota exhausted:", e)
        raise Exception("API_LIMIT_REACHED")

    except Exception as e:
        print(f"Error generating Manim code: {e}")
        return """from manim import *\nimport numpy as np\n\nclass GeneratedScene(Scene):\n    def construct(self):\n        text = Text(\"Error generating animation\", font_size=36)\n        self.play(Write(text))\n        self.wait(2)"""
