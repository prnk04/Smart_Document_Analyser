"""
Testing text summarizer
"""

import pytest
from src.summarizer import summarize_document

from src.llm_client import llm_client


def test_classification():
    result = summarize_document(
        """This Employment Agreement is entered into on January 15, 2024, between TechCorp Inc. ("Employer") and John Smith ("Employee").""",
        llm_client,
        max_length=50,
    )

    assert "summary" in result
    assert "key_points" in result
    assert len(result["summary"].split(" ")) <= 50
