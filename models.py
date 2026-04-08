# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Student Counsellor Environment.

The student_counsellor environment evaluates quality of counsellor responses
based on empathy, encouragement, practical advice, and safety.
"""

from typing import Optional
from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class StudentCounsellorAction(Action):
    """Action for the Student Counsellor environment - counsellor response to student."""

    message: str = Field(
        ..., description="Counsellor's response message to the student"
    )


class StudentCounsellorObservation(Observation):
    """Observation from the Student Counsellor environment."""

    # Task information
    student_message: str = Field(
        default="", description="The student's message/concern"
    )
    task_id: str = Field(default="", description="ID of the current task")
    task_difficulty: str = Field(
        default="", description="Difficulty level: easy, medium, or hard"
    )
    task_description: str = Field(
        default="", description="Description of the student's situation"
    )
    expected_behavior: str = Field(
        default="", description="Expected counsellor behavior for this task"
    )

    # Response information
    counsellor_response: str = Field(
        default="", description="The counsellor's response message"
    )

    # Reward information
    reward: float = Field(default=0.0, description="Reward score from 0.0 to 1.0")
