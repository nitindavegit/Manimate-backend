import subprocess
import os
import sys
import glob
import shutil
import re
import logging

def to_snake_case(name: str) -> str:
    """Convert PascalCase scene name to snake_case (used by Manim for folders)."""
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

def find_generated_video(generate_dir, scene_name="GeneratedScene"):
    """Robust function to find the generated video file in various possible locations."""
    scene_snake = to_snake_case(scene_name)
    
    search_patterns = [
        os.path.join(generate_dir, "videos", scene_snake, "*", "output.mp4"),
        os.path.join(generate_dir, "videos", scene_snake, "output.mp4"),
        os.path.join(generate_dir, "videos", "*", "output.mp4"),
        os.path.join(generate_dir, "videos", "output.mp4"),
        os.path.join(generate_dir, "output.mp4"),
        os.path.join(generate_dir, "**", "output.mp4"),
        os.path.join(generate_dir, "**", f"{scene_name}.mp4"),
        os.path.join(generate_dir, "**", f"{scene_snake}.mp4"),
        os.path.join(generate_dir, "**", "generated_scene.mp4"),
        os.path.join(generate_dir, "**", "*.mp4"),
    ]
    
    for pattern in search_patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            return matches[0]
    
    return None

def write_to_file(code: str, filename="generated_scene.py") -> str:
    """Write code to a Python file in the generate folder and return its full path."""
    generate_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "generate"))
    os.makedirs(generate_dir, exist_ok=True)

    path = os.path.join(generate_dir, filename)
    with open(path, "w") as f:
        f.write(code)
    return path

def cleanup_old_files(generate_dir: str, keep_latest: int = 3):
    """Remove old .mp4 files keeping only the `keep_latest` most recent."""
    try:
        mp4_files = glob.glob(os.path.join(generate_dir, "*.mp4"))
        mp4_files.sort(key=os.path.getmtime, reverse=True)
        for f in mp4_files[keep_latest:]:
            os.remove(f)
    except Exception:
        pass

def run_manim(code: str, scene_name: str = "GeneratedScene"):
    generate_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "generate"))
    os.makedirs(generate_dir, exist_ok=True)

    cleanup_old_files(generate_dir, keep_latest=3)
    filepath = write_to_file(code, "generated_scene.py")

    command = [
        sys.executable, "-m", "manim", filepath, scene_name,
        "-qm", "--output_file", "output",
        "--media_dir", generate_dir
    ]

    last_error = None
    for attempt in range(1, 3):
        try:
            result = subprocess.run(
                command,
                cwd=generate_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                logging.info("Manim rendered successfully.")
                break

            last_error = result.stderr.strip() or result.stdout.strip() or f"Exit code {result.returncode}"
            logging.warning("Attempt %d failed: %s", attempt, last_error[:200])

        except subprocess.TimeoutExpired:
            last_error = "Rendering timed out (over 300 seconds)"
            logging.warning("Attempt %d timed out", attempt)
        except FileNotFoundError as e:
            raise Exception(f"Manim or Python not installed properly: {e}")
        except Exception as e:
            last_error = str(e)
            logging.warning("Attempt %d error: %s", attempt, last_error[:200])

        if attempt == 1:
            logging.info("Retrying rendering...")
        else:
            raise Exception(f"Manim failed after 2 attempts: {last_error}")

    video_file = find_generated_video(generate_dir, scene_name)
    
    if not video_file:
        # list_directory_contents(generate_dir, max_depth=5) # Removed as per edit hint
        raise Exception("❌ Rendered file not found after exhaustive search")

    target_path = os.path.join(generate_dir, "output.mp4")

    if os.path.exists(target_path):
        os.remove(target_path)

    shutil.copy(video_file, target_path)

    # Clean up Manim intermediate files to save disk space
    for subdir in ["videos", "partial_movie_files", "images", "text", "tex"]:
        path = os.path.join(generate_dir, subdir)
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
            except Exception:
                pass

    return "output.mp4"
