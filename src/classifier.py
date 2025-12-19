import json
from src.llm_client import LLMClient


def classify_document(text: str, document_categories: list, llmclient):

    inputPrompt = f""" You are given an excerpt from a document: {text}. Go through this text, and review it carefully. Think:
    1. What type of document is it?
    2. What information does it contain?
    3. What is the topic of this document?

    After making thorough observations, classify the document in one of the given categories{document_categories}. Classify the model into one of the given categories only.
    If it fits multiple categories, pick the one which is fits the best.
    Also, provide reasoning for the classification
    
    Provide valid JSON only of the form:
        {{"category": "the category", "confidence": 0.95, "reasoning": "brief explanation"}}
    
    
    Return ONLY valid JSON
        
    """

    input_list = [
        {
            "role": "system",
            "content": "You are a document classification expert. Always return valid JSON",
        },
        {"role": "user", "content": inputPrompt},
    ]

    try:
        model_response = llmclient.call_model_with_fallback(
            input_list,
            primary_model="gpt-4o-mini",
            primary_timeout=30.0,
            temperature=0.1,
        )
        print("Response from the model for all: ", model_response)
        print(
            model_response.choices[  # pyright: ignore[reportOptionalMemberAccess]
                0
            ].message.content  # pyright: ignore[reportOptionalMemberAccess]
        )  # pyright: ignore[reportOptionalMemberAccess]

        content = model_response.choices[0].message.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()

        return json.loads(content)

    except Exception as e:
        print(llmclient.handle_user_errors(e))
        raise


# if __name__ == "__main__":
#     # Test classification
#     llmclient = LLMClient("llm_cache")
#     result = classify_document(
#         """EMPLOYMENT CONTRACT

#             This Employment Agreement is entered into on January 15, 2024, between TechCorp Inc. ("Employer") and John Smith ("Employee").

#             Position: Senior Software Engineer
#             Start Date: February 1, 2024
#             Salary: $95,000 per annum
#             Location: San Francisco, CA

#             The Employee agrees to perform duties as assigned by the Engineering Manager, Sarah Johnson.

#             Benefits include health insurance, 401(k) matching, and 15 days paid time off annually.

#             This contract may be terminated by either party with 30 days written notice.

#             Signed:
#             TechCorp Inc.
#             John Smith
#             """,
#         document_categories=[
#             "Contract",
#             "Invoice",
#             "Email",
#             "Report",
#             "License",
#             "Contract",
#             "Will",
#             "Certificates",
#             "Technical Spec",
#             "Memo",
#             "Application",
#             "Manuals",
#             "Recipe",
#             "Financial Statement",
#             "Other",
#         ],
#         llmclient=llmclient,
#     )
#     print(result)
