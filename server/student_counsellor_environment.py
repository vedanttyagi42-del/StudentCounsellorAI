# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Student Counsellor Environment Implementation.

A counsellor environment that evaluates quality of responses to student concerns
based on empathy, encouragement, practical advice, and safety checks.
"""

try:
    from ..env import StudentCounsellorEnv
except ImportError:
    from env import StudentCounsellorEnv


# Export the main environment
class StudentCounsellorEnvironment(StudentCounsellorEnv):
   _difficulty_cycle = ["easy", "medium", "hard"]
    _call_count = 0

    def reset(self, task_difficulty: str = None) -> object:
        # Cycle through all 3 difficulties so evaluator sees all tasks
        difficulty = self._difficulty_cycle[
            StudentCounsellorEnvironment._call_count % 3
        ]
        StudentCounsellorEnvironment._call_count += 1
        return super().reset(task_difficulty=difficulty)
