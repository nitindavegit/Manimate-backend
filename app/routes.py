from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.llm_handler import get_manim_code
from app.manim_runner import run_manim
import traceback

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
    
    
@router.post("/",response_model= VideoResponse)
async def generate_video(data: PromptModel):
    try:
        # get the manim code from LLM
        manim_code = get_manim_code(data.prompt)
        
        # render video
        filename = run_manim(manim_code, scene_name="GeneratedScene")
        
        # return video url
        return {"video_url": f"/videos/{filename}"}
        
    except Exception  as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Connection Error: {str(e)}")
