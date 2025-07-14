import logging
import re
from openai import OpenAI, RateLimitError
from app.config import OPENAI_API_KEY, OPENAI_BASE_URL

logging.basicConfig(level=logging.INFO)

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
        "- Text (use `Text(...)`, font_size must be between 36 and 60 only).\n"
        "- Math: use `MathTex(...)` for equations.\n"
        "- Shapes: `Circle`, `Square`, `Dot`, `Line`, `Arrow`, `Rectangle`, `Polygon`.\n"
        "- Graphs: Use `Axes(...).plot(...)`. Label with `axes.get_graph_label(graph, label=\"...\", x_val=...)`.\n"
        "- NEVER add `font_size` to `get_graph_label()` — this is NOT supported in v0.19.0.\n"
        "- Shade area: `axes.get_area(graph, x_range=[a, b], color=..., opacity=0.5)`.\n\n"

        "## SPATIAL & VISUAL RULES\n"
        "- All elements MUST stay inside the visible frame (~14 units wide).\n"
        "- At the end of construct(), group all elements with VGroup(*self.mobjects), then scale_to_fit_width(10) and move_to(ORIGIN).\n"
        "- Separate text labels from diagrams.\n"
        "- Use VGroup(...).arrange(...) with sufficient buff (≥1.5) between labels or diagram parts.\n"
        "- Scale main visuals using .scale_to_fit_width(10) or .scale(0.8) to prevent overflow.\n"
        "- Always place labels above diagram using .next_to(..., UP, buff=0.5).\n"
        "- Avoid text touching other text or objects — use .arrange() and .next_to() consistently.\n\n"

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

        if "Visualization not supported" in raw:
            return raw

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
            raw = raw.replace("class GeneratedScene(Scene):", "class GeneratedScene(ThreeDScene):")

        if "class GeneratedScene" not in raw:
            raise Exception("Generated code must contain a 'GeneratedScene' class")

        # Auto-fix missing self.wait()
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

        # Sanitize font sizes > 64
        raw = re.sub(r"font_size\s*=\s*(\d{3,})", "font_size=60", raw)

        # Inject auto-layout
        if "def construct(self):" in raw:
            try:
                lines = raw.split('\n')
                construct_start = [i for i, line in enumerate(lines) if "def construct(self):" in line][0]
                construct_indent = len(lines[construct_start]) - len(lines[construct_start].lstrip()) + 4
                indent = ' ' * construct_indent

                layout_block = f"\n{indent}try:\n" \
                               f"{indent}    from manim import VMobject\n" \
                               f"{indent}    all_mobs = self.mobjects\n" \
                               f"{indent}    text_labels = [m for m in all_mobs if isinstance(m, Text)]\n" \
                               f"{indent}    non_text = [m for m in all_mobs if isinstance(m, VMobject) and not isinstance(m, Text)]\n" \
                               f"{indent}    diagram = VGroup(*non_text)\n" \
                               f"{indent}    diagram.scale_to_fit_width(10)\n" \
                               f"{indent}    diagram.move_to(ORIGIN)\n" \
                               f"{indent}    if len(text_labels) > 1:\n" \
                               f"{indent}        labels = VGroup(*text_labels).arrange(RIGHT, buff=1.5)\n" \
                               f"{indent}        labels.next_to(diagram, UP, buff=0.5)\n" \
                               f"{indent}    elif len(text_labels) == 1:\n" \
                               f"{indent}        text_labels[0].next_to(diagram, UP, buff=0.5)\n" \
                               f"{indent}except Exception as layout_error:\n" \
                               f"{indent}    pass"

                insert_at = len(lines) - 1
                lines.insert(insert_at, layout_block)
                raw = '\n'.join(lines)
            except Exception as layout_inject_error:
                logging.warning("⚠️ Auto-layout injection failed: %s", layout_inject_error)

        return raw

    except RateLimitError:
        raise Exception("API_LIMIT_REACHED")

    except Exception as e:
        logging.warning("🚫 LLM generation failed: %s", e)
        return (
            "from manim import *\nimport numpy as np\n\n"
            "class GeneratedScene(Scene):\n"
            "    def construct(self):\n"
            "        self.play(Write(Text(\"❌ Error generating animation\", font_size=36)))\n"
            "        self.wait(2)"
        )
