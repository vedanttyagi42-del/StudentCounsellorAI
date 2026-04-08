# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the Student Counsellor Environment.

Flow:
  POST /reset  → start a new episode (no student message needed)
  POST /step   → send student message → AI generates counsellor reply → grader scores it
  GET  /state  → current episode state
  WS   /ws     → WebSocket for persistent sessions
"""

import os

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError("openenv is required. Install with:\n    uv sync\n") from e

try:
    from ..models import StudentCounsellorAction, StudentCounsellorObservation
    from .student_counsellor_environment import StudentCounsellorEnvironment
except (ModuleNotFoundError, ImportError):
    from models import StudentCounsellorAction, StudentCounsellorObservation
    from server.student_counsellor_environment import StudentCounsellorEnvironment

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
# ---------------------------------------------------------------------------
# System prompt for the AI counsellor
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Helper: get OpenAI client
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Create the base OpenEnv app
# ---------------------------------------------------------------------------

app = create_app(
    StudentCounsellorEnvironment,
    StudentCounsellorAction,
    StudentCounsellorObservation,
    env_name="student_counsellor",
    max_concurrent_envs=1,
)


# ---------------------------------------------------------------------------
# Override /step: student_message = what user typed,
#                 counsellor_response = AI-generated reply (then graded)
# ---------------------------------------------------------------------------

from grader import grade_response

SYSTEM_PROMPT = """You are a supportive and intelligent student counsellor and study assistant.

Your main focus is academics, but you also provide emotional support only when needed.

You help students with:
- Academic doubts (explained simply)
- Motivation and encouragement for studies
- Practical study advice
- Creating study plans and daily timetables

Follow these STRICT rules in every response:
1. If the user shows signs of stress, anxiety, or lack of confidence → start with empathy, then encouragement, then practical help.
2. If the user is casually chatting or sending greetings (e.g., "hi", "hello", "yo") → respond in a friendly, neutral way, without assuming they are upset.
3. If the user asks academic questions or for study help → respond clearly and helpfully.
4. Keep explanations simple and short (3–6 sentences)
5. Use simple language suitable for school students
6. Do NOT say anything negative or discouraging
7. Do NOT include emojis

Special behavior:
- For study plans → give step-by-step actionable plan
- For timetables → suggest realistic time blocks
- For doubts → explain like a friendly teacher
- Only give emotional support when it seems necessary
"""


class StepRequest(BaseModel):
    message: str  # This is now the STUDENT's message


def get_openai_client() -> OpenAI:
    """
    Initialize and return an OpenAI client.

    Reads configuration from environment variables:
    - API_BASE_URL: Base URL for the API (default: https://api.openai.com/v1)
    - MODEL_NAME: Model name (default: gpt-3.5-turbo)
    - OPENAI_API_KEY: API key (required)

    Returns:
        OpenAI client instance

    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError(
            "API_KEY environment variable is not set. "
            "Please set it before running inference."
        )

    api_base_url = os.getenv("API_BASE_URL", "https://api.openai.com/v1")

    return OpenAI(api_key=api_key, base_url=api_base_url)


def get_model_name() -> str:
    """
    Get the model name from environment variable.

    Returns:
        Model name (default: gpt-3.5-turbo)
    """
    return os.getenv("MODEL_NAME", "gpt-3.5-turbo")


def generate_counsellor_response(
    client: OpenAI, student_message: str, model_name: str
) -> str:
    """
    Generate a counsellor response using OpenAI API.

    Args:
        client: OpenAI client instance
        student_message: The student's message
        model_name: Name of the model to use

    Returns:
        Generated counsellor response
    """
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": student_message},
        ],
        temperature=0.7,
        max_tokens=500,
    )

    return response.choices[0].message.content


@app.post("/step", response_model=None)
async def step(request: StepRequest):
    try:
        client = get_openai_client()
        model_name = get_model_name()
    except ValueError as e:
        print(f"Error: {e}")
        return
    """
    Receives the student's message, generates an AI counsellor reply,
    grades it, and returns the full observation.
    """
    student_message = request.message.strip()

    if not student_message:
        raise HTTPException(status_code=400, detail="message must not be empty.")
    try:
        counsellor_response = generate_counsellor_response(
            client, student_message, model_name
        )
        print(f"Counsellor Response: {counsellor_response}")
    except Exception as e:
        print(f"Error generating response: {e}")
        print("[END]")
        return

    counsellor_reply = counsellor_response.strip()
    # Step 1: Generate AI counsellor reply

    # Step 2: Grade the counsellor reply

    # Step 3: Return clean observation
    return JSONResponse(
        {
            "observation": {
                "student_message": student_message,
                "counsellor_response": counsellor_reply,
            },
        }
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/")
async def root():
    return JSONResponse({"status": "ok", "env": "student_counsellor"})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)
