# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Environment implementation for the Student Counsellor.

Implements the core OpenEnv Environment interface with reset(), step(),
and state() methods for the Student Counsellor chatbot.
"""

from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from grader import grade_response
from tasks import get_task, Task
from models import StudentCounsellorAction, StudentCounsellorObservation


class StudentCounsellorEnv(Environment):
    """
    Student Counsellor Environment implementation.

    This environment presents counselling tasks to a student and evaluates
    the quality of counsellor responses based on empathy, encouragement,
    practical advice, and safety.

    The environment follows the OpenEnv API with reset(), step(), and state() methods.

    Example:
        >>> env = StudentCounsellorEnv()
        >>> obs = env.reset()
        >>> print(obs.student_message)
        >>> obs = env.step(StudentCounsellorAction(message="I understand your concerns..."))
        >>> print(obs.reward)
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        """Initialize the Student Counsellor environment."""
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._current_task: Task | None = None
        self._done = False
        self._last_reward = 0.0
        self._last_reward_details = {}

    def reset(self, task_difficulty: str = "easy") -> StudentCounsellorObservation:
        """
        Reset the environment and select a new task.

        Returns:
            StudentCounsellorObservation with the task details
        """
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._done = False
        self._last_reward = 0.0
        self._last_reward_details = {}

        # Select random task difficulty for this episode
        # For deterministic behavior, use easy task on reset
        self._current_task = get_task(task_difficulty)

        return StudentCounsellorObservation(
            student_message=self._current_task.input_message,
            task_id=self._current_task.task_id,
            task_difficulty=self._current_task.difficulty,
            task_description=self._current_task.description,
            expected_behavior=self._current_task.expected_behavior,
            counsellor_response="",
            reward=None,
            done=False,
            metadata={"step": 0, "episode_id": self._state.episode_id},
        )

    def step(self, action: StudentCounsellorAction) -> StudentCounsellorObservation:
        """
        Execute a step in the environment.

        Evaluates the counsellor response to the student's message.

        Args:
            action: StudentCounsellorAction containing the counsellor's response

        Returns:
            StudentCounsellorObservation with reward and response details
        """
        if self._done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        if self._current_task is None:
            raise RuntimeError(
                "No task selected. Call reset() to initialize the environment."
            )

        self._state.step_count += 1

        # Grade the response
        reward, reward_details = grade_response(action.message)
        self._last_reward = reward
        self._last_reward_details = reward_details

        # Mark episode as done after one step
        self._done = True

        return StudentCounsellorObservation(
            student_message=self._current_task.input_message,
            task_id=self._current_task.task_id,
            task_difficulty=self._current_task.difficulty,
            task_description=self._current_task.description,
            expected_behavior=self._current_task.expected_behavior,
            counsellor_response=action.message,
            reward=reward,
            done=True,
            metadata={
                "step": self._state.step_count,
                "episode_id": self._state.episode_id,
                "reward_details": reward_details,
            },
        )

    @property
    def state(self) -> State:
        """
        Get the current environment state.

        Returns:
            Current State with episode_id and step_count
        """
        return self._state
