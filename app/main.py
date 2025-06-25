from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import router as generate_router

app = FastAPI(
    title="Manimate API",
    description="Backend service for generating animations from prompts using LLM + Manim.",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Replace "*" with your frontend domain in production
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials = True
)

# Mount static files (video outputs)
app.mount("/videos",StaticFiles(directory="generate"), name="videos")
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Include API routes
app.include_router(generate_router)