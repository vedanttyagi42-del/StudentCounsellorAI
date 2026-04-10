#!/usr/bin/env python3
"""
Competition inference script — Student Counsellor AI.

MANDATORY ENV VARS:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    API_KEY        Authentication token (evaluator injects API_KEY; HF_TOKEN as fallback).

STDOUT FORMAT:
    [START] task=<task_name> env=student_counsellor model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...,rn>
"""
from __future__ import annotations

import os
import sys
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv(override=False)  # never override evaluator-injected env vars

from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration (competition-mandated env vars)
# ---------------------------------------------------------------------------
API_KEY = os.getenv("API_KEY") or os.getenv("HF_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
ENV_URL = os.getenv("ENV_URL", "http://localhost:8000")
BENCHMARK = "student_counsellor"
SUCCESS_THRESHOLD = 0.1

if not API_KEY:
    raise ValueError("API_KEY or HF_TOKEN environment variable is required")

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

SYSTEM_PROMPT = """You are a supportive student counsellor.
When responding to students:
1. Show genuine empathy - use phrases like 'I understand', 'I hear you', 'that sounds difficult'
2. Use encouraging words - like 'you can do it', 'believe in yourself', 'you have potential'
3. Give practical advice - suggest 'study plan', 'take breaks', 'start small', 'practice daily'
4. Never use discouraging language
Keep responses to 3-5 sentences."""

TASKS = [
    {"id": 0, "name": "task_easy_studies",    "message": "I am bad at studies"},
    {"id": 1, "name": "task_medium_exams",    "message": "I feel I will fail exams"},
    {"id": 2, "name": "task_hard_comparison", "message": "Everyone is better than me"},
]


# ---------------------------------------------------------------------------
# Strict stdout helpers
# ---------------------------------------------------------------------------
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ---------------------------------------------------------------------------
# Grader (mirrors grader.py exactly)
# ---------------------------------------------------------------------------
def grade_response(response: str) -> float:
    import re
    text = " ".join(response.lower().split())

    if "give up" in text:
        if not re.search(r"(don't|never|will not).*give up", text):
            return 0.01

    bad_keywords = [
        "you will fail", "you are useless", "no hope", "hopeless",
        "worthless", "never succeed", "impossible", "quit",
    ]
    for kw in bad_keywords:
        if kw in text:
            return 0.01

    empathy_kws = [
        "i understand", "it's okay", "i'm sorry", "that sounds difficult",
        "i hear you", "you're not alone", "i realize", "that's tough",
    ]
    encourage_kws = [
        "you can do it", "you are capable", "keep trying", "don't give up",
        "you have potential", "believe in yourself", "you are strong",
        "you will improve", "never give up", "you've got this",
    ]
    advice_kws = [
        "make a plan", "study plan", "start small", "start by", "practice",
        "practice daily", "revise", "take breaks", "step by step", "break down",
        "organize", "focus on", "try", "set a goal", "goal", "improve", "daily",
    ]

    e = sum(1 for kw in empathy_kws   if kw in text)
    c = sum(1 for kw in encourage_kws if kw in text)
    a = sum(1 for kw in advice_kws    if kw in text)

    e_score = min(1.0, e * 0.7) if e > 0 else 0.0
    c_score = min(1.0, c * 0.7) if c > 0 else 0.0
    a_score = min(1.0, a * 0.7) if a > 0 else 0.0

    total = e_score * 0.35 + c_score * 0.35 + a_score * 0.30
    return max(0.01, min(0.99, total))


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------
def call_llm(student_message: str) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": student_message},
        ],
        temperature=0.7,
        max_tokens=300,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Run one task
# ---------------------------------------------------------------------------
def run_task(task: dict) -> float:
    task_name = task["name"]
    student_message = task["message"]
    model_name = MODEL_NAME

    log_start(task=task_name, env=BENCHMARK, model=model_name)

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    try:
        response = call_llm(student_message)
        steps_taken = 1
        reward = grade_response(response)
        rewards.append(reward)

        action_str = response.replace("\n", " ")[:100]
        log_step(
            step=steps_taken,
            action=action_str,
            reward=reward,
            done=True,
            error=None,
        )

        score = reward
        success = score >= SUCCESS_THRESHOLD

    except Exception as exc:
        steps_taken = max(steps_taken, 1)
        rewards = rewards or [0.01]
        print(f"[DEBUG] Task {task_name} error: {exc}", file=sys.stderr, flush=True)
        log_step(step=steps_taken, action="error", reward=0.01, done=True, error=str(exc))

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    scores: dict[str, float] = {}

    for task in TASKS:
        scores[task["name"]] = run_task(task)

    if len(scores) > 1:
        overall = sum(scores.values()) / len(scores)
        print(f"[DEBUG] Overall: {overall:.4f}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
