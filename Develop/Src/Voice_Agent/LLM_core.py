import os
import json
from typing import Optional

import requests
from dotenv import load_dotenv


load_dotenv(override=True)

EDEN_API_KEY = os.environ.get("EDEN_API_KEY")
if not EDEN_API_KEY:
    EDEN_API_KEY = input("Couldn't find EDEN_API_KEY, enter your API key:\n>>> ").strip()
    if not EDEN_API_KEY:
        raise RuntimeError("No EDEN_API_KEY provided. Aborting.")

def master_LLM(user_query: str, system_prompt: str,
               temperature: float = 0.7,
               max_tokens: int = 1024) -> str:
    """
    Sends a chat request to Eden AI using Google's Gemini 2.5 Flash model.
    
    :param user_query: The user's question or input.
    :param system_prompt: System-level instructions for the model.
    :param temperature: Creativity/variance of output (0.0 – 2.0).
    :param max_tokens: Maximum tokens for the response.
    :return: Assistant's response as a string.
    """

    url = "https://api.edenai.run/v2/llm/chat"

    payload = {
        "model": "google/gemini-2.5-flash",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {EDEN_API_KEY}",
    }

    response = requests.post(url, json=payload, headers=headers)

    if not response.ok:
        raise RuntimeError(
            f"Eden request failed with status {response.status_code}:\n{response.text}"
        )

    data = response.json()

    try:
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
    except Exception:
        pass

    return json.dumps(data, ensure_ascii=False, indent=2)
    
# Example_use
# answer = master_LLM(user_query="سلام", system_prompt=prompt)
# print(answer)