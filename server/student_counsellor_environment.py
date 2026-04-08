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
    """
    Server environment wrapper for Student Counsellor.

    This class extends StudentCounsellorEnv to work with the OpenEnv HTTP server.
    It maintains the same interface and behavior as the core environment.

    Example:

        >>> env = StudentCounsellorEnvironment()
        >>> obs = env.reset()
        >>> print(obs.student_message)
        >>> obs = env.step(StudentCounsellorAction(message="I understand..."))
        >>> print(obs.reward)
    """

    pass
