from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.llm_handler import get_manim_code
from app.manim_runner import run_manim, write_to_file
import traceback
import logging

router = APIRouter(
    prefix="/generate",
    tags=['Generate']
)

# Request Model
class PromptModel(BaseModel):
    prompt: str

# Response Model
class VideoResponse(BaseModel):
    video_url: str

@router.post("/", response_model=VideoResponse)
async def generate_video(data: PromptModel):
    try:
        # Try to get Manim code from LLM
        try:
            manim_code = get_manim_code(data.prompt)
        except Exception as e:
            if "API_LIMIT_REACHED" in str(e):
                logging.warning("⚠️ API limit reached. Returning fallback video.")
                fallback_code = """
from manim import *

class GeneratedScene(Scene):
    def construct(self):
        text = Text("⚠️ API limit reached. Try again tomorrow.", font_size=36, color=YELLOW)
        self.play(Write(text))
        self.wait(2)
"""
                fallback_path = write_to_file(fallback_code, "api_limit_scene.py")
                fallback_video = run_manim(fallback_code, scene_name="GeneratedScene")
                return {"video_url": f"/videos/{fallback_video}"}
            raise  # Reraise if it's not API exhaustion

        # If we got valid code, try rendering
        filename = run_manim(manim_code, scene_name="GeneratedScene")
        return {"video_url": f"/videos/{filename}"}

    except Exception as e:
        logging.warning("⚠️ Primary rendering failed. Falling back to error scene.")
        traceback.print_exc()

        fallback_code = """
from manim import *

class GeneratedScene(Scene):
    def construct(self):
        text = Text("❌ Failed to render animation.", font_size=36, color=RED)
        self.play(Write(text))
        self.wait(2)
"""
        try:
            fallback_path = write_to_file(fallback_code, "fallback_scene.py")
            fallback_video = run_manim(fallback_code, scene_name="GeneratedScene")
            return {"video_url": f"/videos/{fallback_video}"}
        except Exception as fallback_error:
            logging.warning(f"🚨 Fallback rendering also failed: {fallback_error}")
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail="Internal Server Error. Video generation failed completely."
            )