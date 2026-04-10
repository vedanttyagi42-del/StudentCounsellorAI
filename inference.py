# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Inference script for the Student Counsellor Environment.

This script runs the Student Counsellor environment with an OpenAI-based
model to generate counsellor responses to student concerns.

Usage:
    python -m student_counsellor.inference
    python -m student_counsellor.inference --task easy
    python -m student_counsellor.inference --task medium
    python -m student_counsellor.inference --task hard
    python -m student_counsellor.inference --cli

Interactive CLI mode:
    python -m student_counsellor.inference --cli

Environment variables:
    - API_BASE_URL: Base URL for OpenAI API (default: https://api.openai.com/v1)
    - MODEL_NAME: Model to use (default: gpt-3.5-turbo)
    - OPENAI_API_KEY: API key for OpenAI (required)
    - HF_TOKEN: Hugging Face token (optional, for alternative backends)
"""

import os
import sys
import argparse
from typing import Literal
from dotenv import load_dotenv

load_dotenv()
try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package is required. Install with: pip install openai")
    sys.exit(1)

# Handle both module and direct execution
try:
    from .env import StudentCounsellorEnv
    from .models import StudentCounsellorAction
except ImportError:
    # When run directly with python inference.py, use absolute imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from student_counsellor.env import StudentCounsellorEnv
    from student_counsellor.models import StudentCounsellorAction


# System prompt for the counsellor
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


def run_inference(
    task_difficulty: Literal["easy", "medium", "hard"] = "easy",
) -> None:
    """
    Run inference for all tasks (easy, medium, hard).
    Args:
        task_difficulty: Ignored, runs all difficulties to satisfy evaluator requirement of 3 tasks.
    """
    print("[START]")
    print("Initializing Student Counsellor Environment...")

    # Get OpenAI client
    try:
        client = get_openai_client()
        model_name = get_model_name()
        print(f"Using model: {model_name}")
    except ValueError as e:
        print(f"Error: {e}")
        print("[END]")
        return

    # Run all 3 tasks so evaluator sees at least 3 graded results
    for difficulty in ["easy", "medium", "hard"]:
        print(f"\n{'='*50}")
        print(f"Task difficulty: {difficulty}")

        # Initialize a fresh environment per task
        env = StudentCounsellorEnv()

        # Reset environment
        print("\n[STEP] Resetting environment...")
        obs = env.reset(task_difficulty=difficulty)
        print(f"Task ID: {obs.task_id}")
        print(f"Task Difficulty: {obs.task_difficulty}")
        print(f"Task Description: {obs.task_description}")
        print(f"Student Message: {obs.student_message}")
        print(f"Expected Behavior: {obs.expected_behavior}")

        # Generate response
        print("\n[STEP] Generating counsellor response...")
        try:
            counsellor_response = generate_counsellor_response(
                client, obs.student_message, model_name
            )
            print(f"Counsellor Response: {counsellor_response}")
        except Exception as e:
            print(f"Error generating response: {e}")
            continue

        # Step environment
        print("\n[STEP] Evaluating response...")
        action = StudentCounsellorAction(message=counsellor_response)
        result_obs = env.step(action)
        print(f"Reward: {result_obs.reward:.4f}")
        print(f"Done: {result_obs.done}")

        if result_obs.metadata and "reward_details" in result_obs.metadata:
            details = result_obs.metadata["reward_details"]
            empathy = details.get("empathy", 0.0)
            encouragement = details.get("encouragement", 0.0)
            practical_advice = details.get("practical_advice", 0.0)
            empathy_score = empathy * 0.30
            encouragement_score = encouragement * 0.30
            practical_advice_score = practical_advice * 0.30
            print("\nReward Breakdown:")
            print(f"  Empathy: {empathy_score:.4f}")
            print(f"  Encouragement: {encouragement_score:.4f}")
            print(f"  Practical Advice: {practical_advice_score:.4f}")

        # Get final state
        print("\n[STEP] Final state:")
        state = env.state
        print(f"Episode ID: {state.episode_id}")
        print(f"Step Count: {state.step_count}")

    print("\n[END]")

def run_cli_mode() -> None:
    """
    Run the Student Counsellor in interactive CLI mode.

    Provides an interactive terminal-based chat interface where users can
    type messages and receive responses from the AI counsellor.
    Maintains conversation history for context-aware responses.
    """
    print("=" * 70)
    print("STUDENT COUNSELLOR - INTERACTIVE MODE")
    print("=" * 70)
    print("Type your concerns or questions. Type 'exit' or 'quit' to leave.")
    print("=" * 70)

    # Initialize OpenAI client
    try:
        client = get_openai_client()
        model_name = get_model_name()
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Conversation history (store last 10 messages)
    conversation_history = []
    max_history = 10

    # Main interaction loop
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()

            # Check for exit conditions
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            # Skip empty input
            if not user_input:
                continue

            # Add user message to history
            conversation_history.append({"role": "user", "content": user_input})

            # Build messages list with system prompt and history
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
            ]
            messages.extend(conversation_history[-max_history:])

            # Get AI response
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )

            ai_response = response.choices[0].message.content

            # Add AI response to history
            conversation_history.append({"role": "assistant", "content": ai_response})

            # Print AI response
            print(f"AI: {ai_response}")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")
            print("Please try again.")


def main():
    """Main entry point for the inference script."""
    parser = argparse.ArgumentParser(
        description="Run Student Counsellor inference with OpenAI"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in interactive CLI mode",
    )
    parser.add_argument(
        "--task",
        choices=["easy", "medium", "hard"],
        default="easy",
        help="Task difficulty level (default: easy) - ignored if --cli is used",
    )

    args = parser.parse_args()

    # Run CLI mode if requested
    if args.cli:
        run_cli_mode()
    else:
        # Run normal OpenEnv inference mode
        run_inference(task_difficulty=args.task)


if __name__ == "__main__":
    main()
