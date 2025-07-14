import subprocess
import os
import sys
import glob
import shutil
import re

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
    
    print(f"🔍 Searching for video file...")
    print(f"📁 Scene name: {scene_name} (snake_case: {scene_snake})")
    
    for pattern in search_patterns:
        print(f"🔍 Trying pattern: {pattern}")
        matches = glob.glob(pattern, recursive=True)
        if matches:
            print(f"✅ Found {len(matches)} match(es): {matches}")
            return matches[0]
    
    return None

def list_directory_contents(directory, max_depth=3, current_depth=0):
    """Debug function to list directory contents"""
    if current_depth > max_depth:
        return
    
    try:
        items = os.listdir(directory)
        for item in sorted(items):
            item_path = os.path.join(directory, item)
            indent = "  " * current_depth
            if os.path.isdir(item_path):
                print(f"{indent}📁 {item}/")
                list_directory_contents(item_path, max_depth, current_depth + 1)
            else:
                size = os.path.getsize(item_path)
                print(f"{indent}📄 {item} ({size} bytes)")
    except (PermissionError, OSError) as e:
        print(f"{indent}❌ Error reading directory: {e}")

def write_to_file(code: str, filename="generated_scene.py") -> str:
    """Write code to a Python file in the generate folder and return its full path."""
    generate_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "generate"))
    os.makedirs(generate_dir, exist_ok=True)

    path = os.path.join(generate_dir, filename)
    with open(path, "w") as f:
        f.write(code)
    return path

def run_manim(code: str, scene_name: str = "GeneratedScene"):
    generate_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "generate"))
    os.makedirs(generate_dir, exist_ok=True)

    filepath = write_to_file(code, "generated_scene.py")
    print(f"📄 Saving generated code to: {filepath}")

    command = [
        sys.executable, "-m", "manim", filepath, scene_name,
        "-qm", "--output_file", "output",
        "--media_dir", generate_dir
    ]
    print("⚙️ Running command:", " ".join(command))

    try:
        result = subprocess.run(
            command,
            cwd=generate_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
    except KeyboardInterrupt:
        print("⛔ Interrupted by user")
        raise
    except subprocess.TimeoutExpired:
        raise Exception("⏱️ Manim rendering timed out (over 120 seconds).")
    except FileNotFoundError as e:
        raise Exception(f"❌ Manim or Python not installed properly: {e}")
    except Exception as e:
        raise Exception(f"🚨 Unexpected error while running Manim: {e}")

    print("📋 STDOUT:", result.stdout)
    if result.stderr:
        print("📋 STDERR:", result.stderr)

    if result.returncode != 0:
        print("❌ Manim failed")
        error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
        raise Exception(f"🚫 Manim failed: {error_msg}")

    print("✅ Manim rendered successfully.")

    print("\n📁 Directory structure after rendering:")
    list_directory_contents(generate_dir)

    video_file = find_generated_video(generate_dir, scene_name)
    
    if not video_file:
        print("\n❌ Could not find generated video file!")
        print("📁 Full directory listing:")
        list_directory_contents(generate_dir, max_depth=5)
        raise Exception("❌ Rendered file not found after exhaustive search")

    print(f"✅ Found video file: {video_file}")

    target_path = os.path.join(generate_dir, "output.mp4")

    if os.path.exists(target_path):
        os.remove(target_path)

    shutil.copy(video_file, target_path)
    print(f"✅ Copied output from {video_file} to {target_path}")

    return "output.mp4"
