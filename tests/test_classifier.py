"""
Testing classifier
"""

import pytest
from src.classifier import classify_document
from src.llm_client import llm_client


def test_classification():
    categories = ["Contract", "Email", "Report"]
    result = classify_document(
        """This Employment Agreement is entered into on January 15, 2024, between TechCorp Inc. ("Employer") and John Smith ("Employee").""",
        categories,
        llm_client,
    )

    assert "category" in result
    assert "confidence" in result
    assert "reasoning" in result
    assert result["category"] in categories
