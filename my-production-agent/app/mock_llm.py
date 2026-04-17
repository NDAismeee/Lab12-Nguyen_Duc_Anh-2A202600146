import random
import time


_RESPONSES = [
    "Agent is running in production mode (mock response).",
    "This is a mock answer. In production, this would call a real LLM provider.",
    "Request received. Returning a deterministic-ish mock answer.",
]


def ask(question: str) -> str:
    time.sleep(0.05 + random.uniform(0, 0.05))
    if "docker" in question.lower():
        return "Containers package an app + dependencies so it runs consistently across environments."
    if "redis" in question.lower():
        return "Redis is commonly used for caching, rate limiting, and storing session state."
    return random.choice(_RESPONSES)

