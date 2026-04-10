# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Grader for evaluating counsellor responses in the Student Counsellor Environment.
Implements deterministic reward calculation based on empathy, encouragement,
practical advice, and safety checks.
"""

from typing import Tuple


class CounsellorGrader:
    """
    Grades counsellor responses based on quality criteria.
    Implements deterministic reward calculation from 0.0 to 1.0 based on:
    - Empathy: Understanding and acknowledgment of student feelings
    - Encouragement: Positive reinforcement and motivation
    - Practical Advice: Actionable steps the student can take
    - Safety: Avoiding harmful or discouraging language
    """

    # Empathy keywords
    EMPATHY_KEYWORDS = [
        "i understand",
        "it's okay",
        "i'm sorry",
        "that sounds difficult",
        "i hear you",
        "you're not alone",
        "i realize",
        "that's tough",
    ]

    # Encouragement keywords
    ENCOURAGEMENT_KEYWORDS = [
        "you can do it",
        "you are capable",
        "keep trying",
        "don't give up",
        "you have potential",
        "believe in yourself",
        "you are strong",
        "you will improve",
        "never give up",
        "you've got this",
    ]

    # Practical advice keywords
    PRACTICAL_ADVICE_KEYWORDS = [
        "make a plan",
        "study plan",
        "start small",
        "start by",
        "practice",
        "practice daily",
        "revise",
        "take breaks",
        "step by step",
        "break down",
        "organize",
        "focus on",
        "try",
        "try this",
        "set a goal",
        "goal",
        "improve",
        "daily",
    ]

    # Bad keywords that harm student
    BAD_KEYWORDS = [
        "you will fail",
        "you are useless",
        "no hope",
        "give up",
        "hopeless",
        "worthless",
        "never succeed",
        "impossible",
        "quit",
    ]

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Normalize text for comparison.
        Args:
            text: Input text
        Returns:
            Lowercase, whitespace-normalized text
        """
        return " ".join(text.lower().split())

    @staticmethod
    def _count_keyword_matches(text: str, keywords: list[str]) -> int:
        """
        Count how many keywords appear in text.
        Args:
            text: Text to search
            keywords: List of keywords to look for
        Returns:
            Count of keyword matches (each keyword counted once maximum)
        """
        normalized_text = CounsellorGrader._normalize_text(text)
        count = 0
        for keyword in keywords:
            if keyword.lower() in normalized_text:
                count += 1
        return count

    @staticmethod
    def _check_bad_keywords(text: str) -> int:
        """
        Check for bad keywords in text, with context awareness.
        For example, "don't give up" should not count as a bad keyword
        even though "give up" is in the bad keywords list.
        Args:
            text: Text to search
        Returns:
            Count of bad keyword matches
        """
        normalized_text = CounsellorGrader._normalize_text(text)
        count = 0

        # Special handling for "give up" - check if preceded by "don't" or "never"
        if "give up" in normalized_text:
            # Check if it's preceded by negation
            import re

            # Don't count if preceded by "don't", "never", or "will not"
            if not re.search(r"(don't|never|will not).*give up", normalized_text):
                count += 1

        # Check other bad keywords
        other_bad_keywords = [
            "you will fail",
            "you are useless",
            "no hope",
            "hopeless",
            "worthless",
            "never succeed",
            "impossible",
            "quit",
        ]

        for keyword in other_bad_keywords:
            if keyword.lower() in normalized_text:
                count += 1

        return count

    def grade(self, response: str) -> Tuple[float, dict]:
        """
        Grade a counsellor response.
        Args:
            response: The counsellor's response to grade
        Returns:
            Tuple of (reward_score, details_dict)
            - reward_score: Float between 0.0 and 1.0
            - details_dict: Dict with breakdown of scoring
        """
        # Check for bad keywords - immediate disqualification
        bad_keyword_count = self._check_bad_keywords(response)
        if bad_keyword_count > 0:
            return 0.0, {
                "empathy": 0.0,
                "encouragement": 0.0,
                "practical_advice": 0.0,
                "bad_keywords_found": bad_keyword_count,
                "total_reward": 0.0,
            }

        # Count positive keywords
        empathy_count = self._count_keyword_matches(response, self.EMPATHY_KEYWORDS)
        encouragement_count = self._count_keyword_matches(
            response, self.ENCOURAGEMENT_KEYWORDS
        )
        advice_count = self._count_keyword_matches(
            response, self.PRACTICAL_ADVICE_KEYWORDS
        )

        # Calculate component scores (0 to 1)
        # Each component: if found at least once, award base points
        empathy_score = min(1.0, empathy_count * 0.7) if empathy_count > 0 else 0.0
        encouragement_score = (
            min(1.0, encouragement_count * 0.7) if encouragement_count > 0 else 0.0
        )
        advice_score = min(1.0, advice_count * 0.7) if advice_count > 0 else 0.0

        # Combine scores (weighted average)
        # Weight: empathy 35%, encouragement 35%, practical advice 30%
        total_reward = (
            empathy_score * 0.30 + encouragement_score * 0.30 + advice_score * 0.30
        )

        # Clamp between 0 and 1
        total_reward = max(0.01, min(0.99, total_reward))

        details = {
            "empathy": empathy_score,
            "encouragement": encouragement_score,
            "practical_advice": advice_score,
            "empathy_count": empathy_count,
            "encouragement_count": encouragement_count,
            "advice_count": advice_count,
            "bad_keywords_found": 0,
            "total_reward": total_reward,
        }

        return total_reward, details


# Global grader instance
grader = CounsellorGrader()


def grade_response(response: str) -> Tuple[float, dict]:
    """
    Grade a counsellor response using the global grader.
    Args:
        response: The counsellor's response to grade
    Returns:
        Tuple of (reward_score, details_dict)
    """
    return grader.grade(response)
