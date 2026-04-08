# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Student Counsellor Environment."""

# Core modules that don't depend on external libraries
from .models import StudentCounsellorAction, StudentCounsellorObservation
from .grader import CounsellorGrader, grade_response
from .tasks import Task, get_task, get_all_tasks

# Conditional imports for modules that require openenv
try:
    from .env import StudentCounsellorEnv
    from .client import StudentCounsellorEnv as StudentCounsellorClient

    __all__ = [
        "StudentCounsellorAction",
        "StudentCounsellorObservation",
        "StudentCounsellorEnv",
        "StudentCounsellorClient",
        "CounsellorGrader",
        "grade_response",
        "Task",
        "get_task",
        "get_all_tasks",
    ]
except ImportError:
    # OpenEnv not available - still export core components
    __all__ = [
        "StudentCounsellorAction",
        "StudentCounsellorObservation",
        "CounsellorGrader",
        "grade_response",
        "Task",
        "get_task",
        "get_all_tasks",
    ]
