import json
from src.llm_client import LLMClient


def summarize_document(text: str, llmclient, max_length: int = 200):

    inputPrompt = f""" You are given an excerpt from a documenmt: {text}. Go through this text, and review it crefully. Think:
    1. What type of document is it?
    2. What information does it contain?
    3. What is the topic of this document?
    4. Does it contain any named entities?

    After making thorough observations,provide a brief summary of the document in {max_length} words or less. Detail key points in the form of bullet points.
        Return ONLY valid JSON:
        {{
        "summary": "concise summary here",
        "key_points": ["point 1", "point 2", "point 3"]
        }}

    """

    input_list = [
        {
            "role": "system",
            "content": "You are a an expert in summarising documents. Always return valid JSON",
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
        # return model_response.choices[0].message.content
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
#     result = summarize_document(
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
#         llmclient=llmclient,
#     )
#     print(result)
