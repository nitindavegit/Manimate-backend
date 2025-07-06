# 🎬 Manimate Backend

![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi&logoColor=white)
![Manim](https://img.shields.io/badge/Manim-Animation-blueviolet)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![OpenAI](https://img.shields.io/badge/OpenAI-API-green)

> **Turn your text prompts into beautiful math & educational animations!**

---

## 📝 Project Description

**Manimate Backend** is a FastAPI-powered service that transforms natural language prompts into stunning mathematical and educational animations using OpenAI's LLM and the Manim engine. Simply send a prompt, and receive a rendered video—perfect for educators, content creators, and anyone who wants to visualize concepts programmatically.

---

## ✨ Features

- 🚀 **/generate API**: Send a prompt, get a video URL back!
- 🤖 **LLM Integration**: Uses OpenAI to generate Manim code from your ideas.
- 🎥 **Manim Rendering**: Renders animations and manages output files.
- 📂 **Static Video Hosting**: Serves generated videos via `/videos`.
- 🐳 **Docker Support**: Easy deployment anywhere.

---

## 🛠️ Requirements

- Python 3.10+
- [Manim](https://www.manim.community/) & system dependencies (see Dockerfile)
- OpenAI API key

All Python dependencies are in `requirements.txt`.

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=your_openai_base_url  # Optional
```

---

## ⚡ Quickstart

### 🖥️ Local Development

1. **Clone the repo:**
   ```sh
   git clone https://github.com/nitindavegit/Manimate-backend.git
   cd Manimate-backend
   ```
2. **Install system dependencies:**
   ```sh
   sudo apt-get update && sudo apt-get install -y ffmpeg libcairo2-dev libpango1.0-dev texlive-full build-essential pkg-config
   ```
3. **Install Python dependencies:**
   ```sh
   python -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Set up your `.env` file** (see above).
5. **Run the server:**
   ```sh
   uvicorn app.main:app --reload
   ```

### 🐳 Docker

1. **Build the image:**
   ```sh
   docker build -t manimate-backend .
   ```
2. **Run the container:**
   ```sh
   docker run -p 8000:8000 --env-file .env manimate-backend
   ```

---

## 📡 API Usage

### 🎬 Generate Animation

- **POST** `/generate/`
- **Request Body:**
  ```json
  {
    "prompt": "Show a diagram of a client-server API interaction"
  }
  ```
- **Response:**
  ```json
  {
    "video_url": "/videos/output.mp4"
  }
  ```

### 📺 Access Generated Videos

- **GET** `/videos/{filename}`

---

## 🗂️ Project Structure

```
app/
  config.py         # Loads environment variables
  llm_handler.py    # Handles LLM prompt and Manim code generation
  main.py           # FastAPI app entry point
  manim_runner.py   # Runs Manim and manages output files
  routes.py         # API endpoints
generate/           # Stores generated videos and code
requirements.txt    # Python dependencies
Dockerfile          # Docker build instructions
```

---

## 🧪 Testing

Test Manim rendering without the API:

```sh
python app/test_debug.py
```

---

## 📝 Notes

- 💡 Prompts should describe the animation you want. The LLM generates Manim code, which is rendered and returned as a video.
- 🎬 All generated videos are saved in the `generate/` directory and served via `/videos`.
- 🔒 For production, restrict CORS and secure your API keys.

---

## 📄 License

MIT License 