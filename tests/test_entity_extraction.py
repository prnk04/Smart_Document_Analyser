"""
Testing Entity extraction
"""

import pytest
from src.extractor import extract_entity_from_document

from src.llm_client import llm_client


def test_classification():
    result = extract_entity_from_document(
        """This Employment Agreement is entered into on January 15, 2024, between TechCorp Inc. ("Employer") and John Smith ("Employee").""",
        llm_client,
    )

    assert "names" in result
    assert "dates" in result
    assert "amounts" in result
    assert "organizations" in result
