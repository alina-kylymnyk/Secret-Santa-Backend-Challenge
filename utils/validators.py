# -*- coding: utf-8 -*-
"""Validators for Secret Santa Bot"""

import re


class ValidationError(Exception):
    """Exception raised for validation errors"""
    pass


class ParticipantNameValidator:
    """Validator for participant names"""

    MIN_LENGTH = 2
    MAX_LENGTH = 50

    @staticmethod
    def validate_or_raise(name: str) -> None:
        """
        Validate participant name or raise ValidationError

        Args:
            name: Participant name to validate

        Raises:
            ValidationError: If name is invalid
        """
        if not name or not name.strip():
            raise ValidationError("Ім'я не може бути порожнім")

        name = name.strip()

        if len(name) < ParticipantNameValidator.MIN_LENGTH:
            raise ValidationError(
                f"Ім'я занадто коротке (мінімум {ParticipantNameValidator.MIN_LENGTH} символи)"
            )

        if len(name) > ParticipantNameValidator.MAX_LENGTH:
            raise ValidationError(
                f"Ім'я занадто довге (максимум {ParticipantNameValidator.MAX_LENGTH} символів)"
            )

        # Check for invalid characters - allow unicode letters, digits, spaces, hyphens, underscores, dots
        if not re.match(r'^[\w\s\-\.]+$', name, re.UNICODE):
            raise ValidationError(
                "Ім'я може містити тільки літери, цифри, пробіли, дефіси та підкреслення"
            )


def sanitize_name(name: str) -> str:
    """
    Sanitize participant name by removing extra whitespace

    Args:
        name: Name to sanitize

    Returns:
        Sanitized name
    """
    if not name:
        return ""

    # Remove leading/trailing whitespace and collapse multiple spaces
    return " ".join(name.split())
