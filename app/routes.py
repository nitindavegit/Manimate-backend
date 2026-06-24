from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.llm_handler import get_manim_code
from app.manim_runner import run_manim, write_to_file
from app.rate_limiter import rate_limiter
import traceback
import logging

router = APIRouter(
    prefix="/generate",
    tags=['Generate']
)

class PromptModel(BaseModel):
    prompt: str

class VideoResponse(BaseModel):
    video_url: str

FALLBACK_TEMPLATE = """
from manim import *

class GeneratedScene(Scene):
    def construct(self):
        text = Text("{message}", font_size=36, color={color})
        self.play(Write(text))
        self.wait(2)
"""

@router.post("/", response_model=VideoResponse)
async def generate_video(data: PromptModel, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    allowed, wait_time = rate_limiter.is_allowed(client_ip)
    if not allowed:
        msg = f"Rate limit exceeded. Try again in {wait_time} seconds."
        logging.warning("Rate limited: %s", client_ip)
        fallback = FALLBACK_TEMPLATE.format(message=msg, color="YELLOW")
        write_to_file(fallback, "rate_limit_scene.py")
        video = run_manim(fallback, scene_name="GeneratedScene")
        return {"video_url": f"/videos/{video}"}

    try:
        try:
            manim_code = get_manim_code(data.prompt)
        except Exception as e:
            err_str = str(e)
            logging.warning("LLM error: %s", err_str[:200])

            if err_str.startswith("QUOTA_EXHAUSTED"):
                msg = "API credit exhausted. Contact admin."
            elif err_str.startswith("INVALID_API_KEY"):
                msg = "API key invalid. Contact admin."
            elif err_str.startswith("RATE_LIMITED"):
                msg = "Too many requests. Wait a moment and retry."
            elif err_str.startswith("NETWORK_ERROR"):
                msg = "Network error. Check your connection."
            elif err_str.startswith("OPENAI_DOWN"):
                msg = "AI service is down. Try again later."
            else:
                msg = "Failed to generate animation. Try a different prompt."

            fallback = FALLBACK_TEMPLATE.format(message=msg, color="YELLOW")
            write_to_file(fallback, "llm_error_scene.py")
            video = run_manim(fallback, scene_name="GeneratedScene")
            return {"video_url": f"/videos/{video}"}

        filename = run_manim(manim_code, scene_name="GeneratedScene")
        return {"video_url": f"/videos/{filename}"}

    except Exception as e:
        logging.warning("Rendering failed. Falling back to error scene.")
        traceback.print_exc()

        err_msg = str(e)
        if "timed out" in err_msg.lower():
            msg = "Animation too complex. Try a simpler prompt."
        elif "manim failed" in err_msg.lower():
            msg = "Rendering failed. Try a different prompt."
        else:
            msg = "Something went wrong. Try again."

        fallback = FALLBACK_TEMPLATE.format(message=msg, color="RED")
        try:
            write_to_file(fallback, "fallback_scene.py")
            video = run_manim(fallback, scene_name="GeneratedScene")
            return {"video_url": f"/videos/{video}"}
        except Exception as fb_err:
            logging.warning("Fallback rendering also failed: %s", fb_err)
            raise HTTPException(status_code=500, detail="Video generation failed completely.")
