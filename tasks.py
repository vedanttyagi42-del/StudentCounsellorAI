# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Task definitions for the Student Counsellor Environment.

Defines easy, medium, and hard tasks that students face,
each with specific input messages and expected counselling behavior.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class Task:
    """Represents a counselling task."""

    task_id: str
    input_message: str
    description: str
    difficulty: Literal["easy", "medium", "hard"]
    expected_behavior: str


# Task definitions
TASKS = {
    "easy": Task(
        task_id="task_easy_studies",
        input_message="I am bad at studies",
        description="Student expressing self-doubt about academic abilities",
        difficulty="easy",
        expected_behavior="Provide empathetic response with encouragement. "
        "Acknowledge their concern, reassure them that many students feel this way, "
        "and suggest practical steps like creating a study plan or seeking help.",
    ),
    "medium": Task(
        task_id="task_medium_exams",
        input_message="I feel I will fail exams",
        description="Student experiencing exam stress and anxiety about failure",
        difficulty="medium",
        expected_behavior="Show deep empathy for exam stress. Encourage them to focus on preparation "
        "rather than the outcome. Provide practical advice like breaking study into smaller chunks, "
        "revising regularly, and taking breaks.",
    ),
    "hard": Task(
        task_id="task_hard_comparison",
        input_message="Everyone is better than me",
        description="Student experiencing severe self-doubt through comparison with peers",
        difficulty="hard",
        expected_behavior="Strongly empathize with feelings of inadequacy. Challenge the comparison mindset. "
        "Encourage self-belief and unique strengths. Provide practical advice on focusing on personal growth "
        "rather than comparison, and suggest maintaining realistic perspectives.",
    ),
}


def get_task(difficulty: Literal["easy", "medium", "hard"]) -> Task:
    """
    Get a task by difficulty level.

    Args:
        difficulty: One of 'easy', 'medium', or 'hard'

    Returns:
        Task object with the task details
    """
    return TASKS[difficulty]


def get_all_tasks() -> dict[str, Task]:
    """
    Get all available tasks.

    Returns:
        Dictionary of all tasks indexed by difficulty
    """
    return TASKS
