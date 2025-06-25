from openai import OpenAI
from app.config import OPENAI_API_KEY,OPENAI_BASE_URL
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url= OPENAI_BASE_URL
)

def get_manim_code(prompt: str) -> str:
    system_prompt = "You are a Manim expert. Generate Python code using Manim to visualize:"
    response = client.chat.completions.create(
        model="gpt-4",
        messages= [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content