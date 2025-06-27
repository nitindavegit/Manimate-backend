import subprocess
import os

def run_manim(code: str, scene_name: str = "GeneratedScene"):
    
    # Get absolute path to 'generate/' folder outside 'app/'
    generate_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),"..","generate"))
    os.makedirs(generate_dir,exist_ok=True)
    
    filepath = os.path.join(generate_dir,"generated_scene.py")
    
    with open(filepath,"w") as f:
        f.write(code)
        
    print("Writing to:", os.path.abspath(filepath))
    print("File exists?", os.path.exists(filepath))
    result = subprocess.run([
        "manim", filepath, scene_name, "-ql", "--output_file", "output"
    ], capture_output=True, text= True,timeout=60)  
    if result.returncode != 0:
        print("❌ Manim failed")
        print("▶️ Return code:", result.returncode)
        print("STDOUT:", repr(result.stdout))
        print("STDERR:", repr(result.stderr))
        error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
        raise Exception(f"Manim failed: {error_msg}")
        # raise Exception(f"Manim failed: {result.stderr}")
    
    return "output.mp4"