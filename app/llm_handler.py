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
        "You are a Manim Community v0.19.0 expert producing clean, well-positioned, always-valid Python code.\n\n"

        "## FORMAT\n"
        "- Output ONLY valid Python code — no markdown, no explanations.\n"
        "- Start with:\n"
        "    from manim import *\n"
        "    import numpy as np\n"
        "- Define exactly ONE class: `GeneratedScene(Scene)` (2D) or `GeneratedScene(ThreeDScene)` (3D).\n"
        "- Must have `def construct(self):` ending with `self.wait(2)`.\n\n"

        "## ELEMENTS\n"
        "- Text: `Text(\"...\", font_size=36)` — font_size between 24 and 60.\n"
        "- Math: `MathTex(...)` for equations.\n"
        "- Shapes: `Circle`, `Square`, `Dot`, `Line`, `Arrow`, `Rectangle`, `Polygon`.\n"
        "- Graphs: `Axes(...).plot(...)`. Label with `axes.get_graph_label(graph, label=\"...\", x_val=...)`.\n"
        "- NEVER add `font_size` to `get_graph_label()`.\n"
        "- Shade: `axes.get_area(graph, x_range=[a, b], color=..., opacity=0.3)`.\n\n"

        "## LAYOUT RULES (CRITICAL — elements MUST NOT overlap or go off-screen)\n"
        "- Frame is ~14 units wide × ~8 units tall. Keep everything within these bounds.\n"
        "- Use `scale_to_fit_width(8)` on large elements to ensure they fit with margin.\n"
        "- Use `VGroup(...).arrange(RIGHT, buff=1.0)` or `.arrange(DOWN, buff=0.8)` to space elements.\n"
        "- Place text labels above visuals with `.next_to(visual, UP, buff=0.5)`.\n"
        "- For multi-part scenes, use `VGroup(...).arrange(DOWN, buff=1.0)` to stack sections vertically.\n"
        "- Keep at most 4-5 elements visible at once to avoid clutter.\n"
        "- If showing a sequence (like Fibonacci numbers), show at most 6-8 terms.\n"
        "- Use `MathTex` for ALL formulas — never use `Text` with math symbols.\n\n"

        "## ANIMATIONS\n"
        "- Use `Write`, `Create`, `FadeIn`, `Transform`, `FadeOut`, `Uncreate`.\n"
        "- Keep total animation count between 3 and 10 for clarity.\n\n"

        "## 3D\n"
        "- Use `ThreeDScene` with `self.set_camera_orientation(phi=75*DEGREES, theta=30*DEGREES)`.\n"
        "- Valid 3D: `Surface`, `ThreeDAxes`, `Sphere`, `Cube`, `Cylinder`.\n"
        "- NO `ParametricSurface` — use `Surface(...)`.\n\n"

        "## IMPORTANT: Do NOT add final layout/grouping code at the end of construct(). "
        "The system handles final positioning. Just create and animate your elements.\n\n"

        "## FALLBACK (if concept is not visualizable)\n"
        "from manim import *\n"
        "import numpy as np\n\n"
        "class GeneratedScene(Scene):\n"
        "    def construct(self):\n"
        "        self.play(Write(Text(\"Visualization not supported\", font_size=36, color=RED)))\n"
        "        self.wait(2)\n\n"

        "Generate clean, organized, educational animations. Every element must be clearly visible and spaced."
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

        # Sanitize font sizes: cap anything over 60
        def _cap_font_size(m):
            val = int(m.group(1))
            return f"font_size={min(val, 60)}"
        raw = re.sub(r"font_size\s*=\s*(\d+)", _cap_font_size, raw)

        # Inject smart auto-layout (runs BEFORE self.wait() so layout is visible)
        if "def construct(self):" in raw:
            try:
                lines = raw.split('\n')
                construct_start = [i for i, line in enumerate(lines) if "def construct(self):" in line][0]
                construct_indent = len(lines[construct_start]) - len(lines[construct_start].lstrip()) + 4
                indent = ' ' * construct_indent

                # Find the last self.wait() to insert layout BEFORE it
                wait_indices = [i for i, line in enumerate(lines) if "self.wait(" in line]
                insert_at = wait_indices[-1] if wait_indices else len(lines) - 1

                layout_block = (
                    f"\n{indent}# Smart auto-layout\n"
                    f"{indent}try:\n"
                    f"{indent}    _mobs = [m for m in self.mobjects if m in self.mobjects]\n"
                    f"{indent}    _texts = [m for m in _mobs if isinstance(m, Text)]\n"
                    f"{indent}    _math = [m for m in _mobs if isinstance(m, MathTex)]\n"
                    f"{indent}    _visuals = [m for m in _mobs if isinstance(m, VMobject) and not isinstance(m, (Text, MathTex))]\n"
                    f"\n"
                    f"{indent}    SAFE_W, SAFE_H = 12, 7\n"
                    f"\n"
                    f"{indent}    # 1. Scale + center visual elements (shapes, graphs, etc.)\n"
                    f"{indent}    if _visuals:\n"
                    f"{indent}        _vg = VGroup(*_visuals)\n"
                    f"{indent}        _s = min(SAFE_W / max(_vg.width, 0.01), SAFE_H / max(_vg.height, 0.01), 1.0)\n"
                    f"{indent}        if _s < 1.0:\n"
                    f"{indent}            _vg.scale(_s)\n"
                    f"{indent}        _vg.move_to(ORIGIN)\n"
                    f"\n"
                    f"{indent}    # 2. Position math below visuals\n"
                    f"{indent}    if _math:\n"
                    f"{indent}        _mg = VGroup(*_math)\n"
                    f"{indent}        if len(_math) > 1:\n"
                    f"{indent}            _mg.arrange(DOWN, buff=0.5)\n"
                    f"{indent}        _mg.scale_to_fit_width(min(SAFE_W, _mg.width))\n"
                    f"{indent}        if _visuals:\n"
                    f"{indent}            _mg.next_to(_vg, DOWN, buff=0.5)\n"
                    f"{indent}        else:\n"
                    f"{indent}            _mg.move_to(ORIGIN)\n"
                    f"\n"
                    f"{indent}    # 3. Position text labels above everything\n"
                    f"{indent}    if _texts:\n"
                    f"{indent}        _tg = VGroup(*_texts)\n"
                    f"{indent}        if len(_texts) > 1:\n"
                    f"{indent}            _tg.arrange(RIGHT, buff=0.8)\n"
                    f"{indent}        _tg.scale_to_fit_width(min(SAFE_W, _tg.width))\n"
                    f"{indent}        if _visuals:\n"
                    f"{indent}            _tg.next_to(_vg, UP, buff=0.5)\n"
                    f"{indent}        elif _math:\n"
                    f"{indent}            _tg.next_to(_mg, UP, buff=0.5)\n"
                    f"{indent}        else:\n"
                    f"{indent}            _tg.move_to(ORIGIN)\n"
                    f"\n"
                    f"{indent}    # 4. Final bounds check — nudge anything that drifted off-screen\n"
                    f"{indent}    for _m in self.mobjects:\n"
                    f"{indent}        if hasattr(_m, 'get_center'):\n"
                    f"{indent}            _x, _y = _m.get_center()[:2]\n"
                    f"{indent}            if abs(_x) > 6.5:\n"
                    f"{indent}                _m.shift(LEFT * (_x - 6.0 * (1 if _x > 0 else -1)))\n"
                    f"{indent}            if abs(_y) > 3.5:\n"
                    f"{indent}                _m.shift(DOWN * (_y - 3.0 * (1 if _y > 0 else -1)))\n"
                    f"{indent}except Exception:\n"
                    f"{indent}    import logging\n"
                    f"{indent}    logging.warning(\"Auto-layout skipped\", exc_info=True)\n"
                )

                lines.insert(insert_at, layout_block)
                raw = '\n'.join(lines)
            except Exception as layout_inject_error:
                logging.warning("Auto-layout injection failed: %s", layout_inject_error)

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
