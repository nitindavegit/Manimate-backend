import subprocess
import os

def run_manim(code: str, scene_name: str = "GeneratedScene"):
    filepath = "generate/generated_scene.py"
    
    with open(filepath,"w") as f:
        f.write(code)
        
    result = subprocess.run([
        "manim", filepath, scene_name, "-ql", "--output_file", "output"
    ], cwd="generate", capture_output=True, text= True)
    
    if result.returncode != 0:
        raise Exception(f"Manim failed: {result.stderr}")
    
    return "output.mp4"