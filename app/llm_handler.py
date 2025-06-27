from openai import OpenAI
from app.config import OPENAI_API_KEY,OPENAI_BASE_URL
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url= OPENAI_BASE_URL
)

def get_manim_code(prompt: str) -> str:
    system_prompt = (
        "You are a Manim expert. Your sole task is to generate valid Python code using the Manim library to visualize the prompt provided by the user. "
        "The code must be complete and self-contained, importing all necessary modules. "
        "Always name the scene class as 'GeneratedScene'. "
        "Never include any explanation, comment, markdown formatting, or natural language of any kind. "
        "Do not include triple quotes, code block markers (like ```), or any descriptive text before or after the code. "
        "Only return plain Python code—no extra whitespace, comments, or instructions of any kind. "
        "Output must start directly with the 'from manim import *' line."
        "Ensure self.wait() will be there in the code and must be present at the last line"
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages= [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    print(response)
    raw =  response.choices[0].message.content
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        raw = raw.replace("python\n","",1).strip("`")
    if "self.wait()" not in raw:
        raw += "\n        self.wait()\n"
        
    
    return raw    
    