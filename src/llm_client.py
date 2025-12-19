"""
Here, we will call the LLM model to get the results.
We are going to use:
- exponential backoff with retry
- fallback strategy to use in case a model faile
- error handling
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from openai import (
    OpenAI,
    APIConnectionError,
    APITimeoutError,
    APIError,
    InternalServerError,
    RateLimitError,
    BadRequestError,
)
from typing import Dict, Any, Optional
import hashlib
import json
import time

load_dotenv()


class LLMClient:

    def __init__(self, cache_dir: str = "llm_cache") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    # =========================================================================================#
    #           Operations related to storing/fetching model response to/from cache           #
    # =========================================================================================#

    def _get_cache_key(
        self, messages: list, model: str, temperature: float = 0.7
    ) -> bytes:
        contents = json.dumps(
            {"messages": messages, "model": model, "temperature": temperature},
            sort_keys=True,
        )

        return hashlib.md5(contents.encode()).digest()

    def set(
        self, messages: list, model: str, temperature: float, result: Dict, ttl: int
    ) -> None:
        # get the cache key
        """
        Docstring for set

        :param self
        :param messages: List of input prompts that will be given to the model
        :type messages: list
        :param model: The LLM model that was used to get the response
        :type model: str
        :param temperature: Level of creativity allowed for the model
        :type temperature: float
        :param result: Data that should be stored in the cache file
        :type result: Dict
        """
        cache_file_name = self._get_cache_key(messages, model, temperature)
        cacheFile = self.cache_dir / f"{cache_file_name}.json"

        dataToStore = dict()

        """
        Cache file contents:
        "key" : <key>,
        "value":<data returned by the model>,
        "model": <model used for prediction",
        "temperature":<temperature given to the model>,
        "promptTokens":<number of tokens in the message>,
        "completedTokens": <number of tokens in the output>,
        "totalTokens":<total tokens used in this request>,
        "createdAt":<time of creation>,
        "expiresAt": <time of expiry>
        "lastAccessedAt": <time at which the data was last accessed>,
        "accessCount":<number of times this data has been accessed>
        """

        if cacheFile.exists():
            with open(cache_file_name, "r") as f:
                fileContents = json.load(f)
            dataToStore = fileContents
            dataToStore["lastAccessedAt"] = time.time()
            dataToStore["accessCount"] += 1

        else:
            dataToStore["key"] = cache_file_name
            dataToStore["value"] = result["content"]
            dataToStore["model"] = model
            dataToStore["temperature"] = temperature
            dataToStore["promptTokens"] = result["tokens"]["promptTokens"]
            dataToStore["completedTokens"] = result["tokens"]["completedTokens"]
            dataToStore["totalTokens"] = result["tokens"]["totalTokens"]
            dataToStore["createdAt"] = time.time()
            dataToStore["expiresAt"] = time.time() + ttl
            dataToStore["lastAccessedAt"] = time.time()
            dataToStore["accessCount"] = 0

        with open(cacheFile, "w") as f:
            json.dump(dataToStore, f)

    def get(
        self, messages: list, model: str, temperature: float = 0.7, ttl: int = 86400
    ) -> Any | None:
        cache_key = self._get_cache_key(messages, model, temperature)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        # Load cache entry
        with open(cache_file, "r") as f:
            entry = json.load(f)

        # Check expiry (your idea!)
        created_at = entry.get("created_at", 0)
        age = time.time() - created_at

        if age > ttl:
            # Expired! Delete it
            cache_file.unlink()
            return None

        return entry

    # =============================================================================================================#
    #       Operations related to fetching data from LLM model using retry and fallback with cost estimation      #
    # =============================================================================================================#

    def _call_model_with_retry(
        self,
        messages: list,
        model: str,
        temperature: float = 0.7,
        maxRetries: int = 3,
        initial_delay: float = 1.0,
        timeout: float = 10,
    ):

        # first, create client for the model and call it
        client = OpenAI(timeout=timeout)

        for attempt in range(maxRetries):
            try:
                model_response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    timeout=timeout,
                )

                print(f"Got result in {attempt+1} tries")
                print("response form model: ", model_response)
                return model_response

            except RateLimitError:
                if attempt < maxRetries - 1:
                    print(
                        f"Rate limit reached for retry number: {attempt+1}/{maxRetries}"
                    )
                    print("Will try again afetr delay")
                    delay = initial_delay * (2**attempt)
                    time.sleep(delay)
                else:
                    print(f"Rate limit reached after {maxRetries} attempts")
                    raise

            except InternalServerError:
                if attempt < maxRetries - 1:
                    print(
                        f"Internal server error for retry number: {attempt+1}/{maxRetries}"
                    )
                    print("Will try again afetr delay")
                    delay = initial_delay * (2**attempt)
                    time.sleep(delay)
                else:
                    print(f"Internal server error after {maxRetries} attempts")
                    raise

            except APITimeoutError:
                if attempt < maxRetries - 1:
                    print(f"API timed out for retry number: {attempt+1}/{maxRetries}")
                    print("Will try again afetr delay")
                    delay = initial_delay * (2**attempt)
                    time.sleep(delay)
                else:
                    print(f"API timed out after {maxRetries} attempts")
                    raise

            except APIConnectionError:
                if attempt < maxRetries - 1:
                    print(
                        f"API facing connection issue for retry number: {attempt+1}/{maxRetries}"
                    )
                    print("Will try again afetr delay")
                    delay = initial_delay * (2**attempt)
                    time.sleep(delay)
                else:
                    print(f"API connection failed after {maxRetries} attempts")
                    raise

            except APIError as apie:
                print("API error: ", apie)
                if (
                    hasattr(apie, "status_code")
                    and apie.status_code  # pyright: ignore[reportAttributeAccessIssue]
                    < 500  # pyright: ignore[reportAttributeAccessIssue]
                ):
                    print(
                        f"❌ Client error (status {apie.status_code}): {apie}"  # pyright: ignore[reportAttributeAccessIssue]
                    )  # pyright: ignore[reportAttributeAccessIssue]
                    raise
                elif attempt < maxRetries - 1:
                    print(f"API Error for retry attempt {attempt+ 1}/{maxRetries}")
                    print(f"Error {str(apie)}")
                    delay = initial_delay * (2**attempt)
                    print(f"Retrying after {str(object=delay)}ms")
                    time.sleep(delay)
                else:
                    print(f"API errored out after {maxRetries} attempts")
                    raise

            except Exception as e:
                print(f"Unhandled exception occurred: {type(e)}: {e}")
                raise

        return None

    def handle_user_errors(self, error: Exception) -> str:
        error_map = {
            RateLimitError: "Our AI service is experiencing high demand. Please try again in a moment.",
            APITimeoutError: "The request took too long. Please try again with a shorter input.",
            APIConnectionError: "Unable to connect to AI service. Please check your internet connection.",
            InternalServerError: "We're having trouble processing the response. Please try again.",
            json.JSONDecodeError: "We're having trouble processing the response. Please try again.",
        }

        # Get user-friendly message
        error_type = type(error)
        user_message = error_map.get(
            error_type, "An unexpected error occurred. Please try again."
        )

        # Log technical details (in production, send to logging service)
        print(f"\n[Internal Error Log]")
        print(f"Type: {error_type.__name__}")
        print(f"Message: {str(error)}")
        print(f"User sees: {user_message}\n")

        return user_message

    def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        completion_tokens: int,
    ) -> float:
        prices = {
            "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
            "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
            "gpt-4-turbo": {
                "input": 10.00 / 1_000_000,
                "output": 30.00 / 1_000_000,
            },
        }

        if model not in prices:
            model = "gpt-4o-mini"  # Default

        input_cost = input_tokens * prices[model]["input"]
        output_cost = completion_tokens * prices[model]["output"]

        return input_cost + output_cost

    def call_model_with_fallback(
        self,
        messages: list,
        primary_model: str = "gpt-4o",
        primary_max_retries: int = 1,
        primary_timeout: float = 10,
        fallback_model: str = "gpt-4o-mini",
        fallback_max_retries: int = 3,
        fallback_timeout: float = 20.0,
        temperature: float = 0.7,
        cache_ttl: int = 86400,
        use_cache: bool = True,
    ):
        try:
            print("Trying with model: ", primary_model)

            resultToShow = {}
            # check cache
            if use_cache and temperature == 0.0:
                cached_result = self.get(
                    messages, primary_model, temperature, cache_ttl
                )
                if cached_result:
                    print(f"We have found ressult in the cache: {cached_result}")
                    self.set(
                        messages, primary_model, temperature, cached_result, cache_ttl
                    )

                    return cached_result["value"]

            # since we do not have cached result, let's call the API

            try:
                model_res = self._call_model_with_retry(
                    messages,
                    primary_model,
                    temperature,
                    primary_max_retries,
                    1.0,
                    primary_timeout,
                )
                print("Response from primary model: ", model_res)

                if model_res:
                    result = {
                        "content": model_res.choices[0].message.content,
                        "tokens": {
                            "promptTokens": model_res.usage.prompt_tokens,  # pyright: ignore[reportOptionalMemberAccess]
                            "completedTokens": model_res.usage.completion_tokens,  # pyright: ignore[reportOptionalMemberAccess]
                            "totalTokens": model_res.usage.total_tokens,  # pyright: ignore[reportOptionalMemberAccess]
                        },
                    }

                    if use_cache and temperature == 0.0:
                        self.set(
                            messages, primary_model, temperature, result, cache_ttl
                        )
                    return model_res
            except (
                RateLimitError,
                APITimeoutError,
                InternalServerError,
                APIConnectionError,
            ) as e:
                print(
                    f"⚠️  Primary failed ({type(e).__name__}), trying fallback: {fallback_model}"
                )
                try:
                    fallback_res = self._call_model_with_retry(
                        messages,
                        fallback_model,
                        temperature,
                        fallback_max_retries,
                        1.0,
                        fallback_timeout,
                    )

                    print("Response from fallback model: ", fallback_res)

                    if fallback_res:
                        result = {
                            "content": fallback_res.choices[0].message.content,
                            "tokens": {
                                "promptTokens": fallback_res.usage.prompt_tokens,  # pyright: ignore[reportOptionalMemberAccess]
                                "completedTokens": fallback_res.usage.completion_tokens,  # pyright: ignore[reportOptionalMemberAccess]
                                "totalTokens": fallback_res.usage.total_tokens,  # pyright: ignore[reportOptionalMemberAccess]
                            },
                        }

                        if use_cache and temperature == 0.0:
                            self.set(
                                messages, primary_model, temperature, result, cache_ttl
                            )
                    return fallback_res
                except Exception as fallback_error:
                    raise fallback_error
            except Exception as e:
                print(f"Exception on calling with fallback: {e}")
                raise

        except Exception as e:
            messageToShow = self.handle_user_errors(e)
            print(messageToShow)


llm_client = LLMClient(cache_dir="llm_client")
# =============================================================================================================#
#            Functions to actually classify, summarize, and extract entities form the given document           #
# =============================================================================================================#

# document_categories = [
#     "Contract",
#     "Invoice",
#     "Email",
#     "Report",
#     "License",
#     "Contract",
#     "Will",
#     "Certificates",
#     "Technical Spec",
#     "Memo",
#     "Application",
#     "Manuals",
#     "Recipe",
#     "Financial Statement",
#     "Other",
# ]

# schema = {
#     "names": "list of person names",
#     "dates": "list of dates mentioned",
#     "amounts": "list of monetary amounts",
#     "organizations": "list of organizations/companies",
# }


# def classifty_extract_summarize_document(text: str, max_words: int = 200):

#     user_prompt = f"""Given an expert of the document: {text}, review it carefully. Think carfully:
#     1. What is the topic of this text?
#     2. What does this text want to convey?
#     3. What type of document is this?
#     4. Are there any entities mentioned in the text, like any names, dates, organizations, amounts etc.?

#     Based on your observations, provide the following details about the document:

#     1. Given the list of categories: {document_categories}:
#         1.1. Which category does it fit the best?
#         1.2. Why does it fit this category?

#         Provide valid JSON only of the form:
#         {{"category": "the category", "confidence": 0.95, "reasoning": "brief explanation"}}

#     2. Extract entities from the document.
#         Return ONLY this JSON structure:
#         {json.dumps(schema, indent=2)}

#         Only include entities actually found in the text.

#     3. Provide a brief summary of the document in {max_words} words. Detail key points in the form of bullet points.
#         Return ONLY valid JSON:
#         {{
#         "summary": "concise summary here",
#         "key_points": ["point 1", "point 2", "point 3"]
#         }}

#     Provide all of these details in the following valid JSON format:

#     {{
#         "classification": {{
#         "category": "the category", "confidence": 0.95, "reasoning": "brief explanation"
#         }},
#         "entities" :<entities>,
#         "summary_details: {{
#         "summary": "concise summary here",
#         "key_points": ["point 1", "point 2", "point 3"]
#         }}
#     }}


#     """

#     input_list = [
#         {
#             "role": "system",
#             "content": "You are an expert document analyst, who reviews documents of comapnies, government, financial sectors, etc, and provide their summaries, what category those documents belong to, and what entities are present in the document",
#         },
#         {"role": "user", "content": user_prompt},
#     ]

#     llmclient = LLMClient("llm_cache")
#     try:
#         model_response = llmclient.call_model_with_fallback(
#             input_list,
#             primary_model="gpt-4o-mini",
#             primary_timeout=30.0,
#             temperature=0.1,
#         )
#         print("Response from the model for all: ", model_response)
#         print(
#             model_response.choices[  # pyright: ignore[reportOptionalMemberAccess]
#                 0
#             ].message.content  # pyright: ignore[reportOptionalMemberAccess]
#         )  # pyright: ignore[reportOptionalMemberAccess]
#     except Exception as e:
#         print(llmclient.handle_user_errors(e))


# if __name__ == "__main__":
#     classifty_extract_summarize_document(
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
#             """
#     )
