"""
nlp_service.py
---------------
Handles the two core AI tasks described in the architecture diagram:

1. Theme extraction from an event description, using DistilBERT run as a
   zero-shot classifier against a configurable candidate-label set.
2. Conversation-starter generation, using GPT-2 conditioned on a prompt built
   from the extracted themes + the user's stated interests.

Models are loaded lazily (on first use) and cached as module-level globals so
the (slow) download/initialization only happens once per process, not once
per request.
"""

import re
from functools import lru_cache
from typing import List

from transformers import pipeline

# Candidate themes the zero-shot classifier chooses from. Extend this list to
# fit the kinds of events your users attend.
CANDIDATE_THEMES = [
    "artificial intelligence", "sustainability", "climate change", "urban planning",
    "healthcare", "finance", "blockchain", "entrepreneurship", "marketing",
    "design", "education", "cybersecurity", "data science", "biotechnology",
    "robotics", "cloud computing", "renewable energy", "public policy",
    "social impact", "product management", "leadership", "venture capital",
]


@lru_cache(maxsize=1)
def _get_theme_classifier():
    # distilbert-base-uncased-mnli is a lightweight model well suited to
    # zero-shot classification without requiring a GPU.
    return pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")


@lru_cache(maxsize=1)
def _get_generator():
    return pipeline("text-generation", model="gpt2")


def extract_themes(event_description: str, top_k: int = 3) -> List[str]:
    """Run zero-shot classification over CANDIDATE_THEMES and return the
    top_k highest-scoring labels for the given event description."""
    classifier = _get_theme_classifier()
    result = classifier(event_description, candidate_labels=CANDIDATE_THEMES, multi_label=True)
    # result["labels"] is already sorted by descending score
    return result["labels"][:top_k]


def _clean_generated_text(text: str, prompt: str) -> str:
    """Strip the prompt echo and trim to a single reasonable sentence/question."""
    generated = text[len(prompt):].strip() if text.startswith(prompt) else text.strip()
    # Cut at the first sentence-ending punctuation to keep starters short.
    match = re.search(r"[.!?]", generated)
    if match:
        generated = generated[: match.end()]
    generated = generated.replace("\n", " ").strip()
    return generated


def generate_conversation_starters(
    themes: List[str],
    interests: List[str],
    bio: str = "",
    num_starters: int = 3,
) -> List[str]:
    """Generate `num_starters` conversation starters using GPT-2, conditioned
    on the extracted themes and the user's interests/bio."""
    generator = _get_generator()
    theme_str = ", ".join(themes) if themes else "networking"
    interest_str = ", ".join(interests) if interests else "meeting new people"

    starters = []
    seen = set()
    attempts = 0
    max_attempts = num_starters * 4  # allow retries for de-duplication

    while len(starters) < num_starters and attempts < max_attempts:
        attempts += 1
        prompt = (
            f"A friendly, curious conversation starter about {theme_str} "
            f"for someone interested in {interest_str}: \""
        )
        output = generator(
            prompt,
            max_new_tokens=40,
            num_return_sequences=1,
            do_sample=True,
            top_p=0.92,
            temperature=0.9,
            pad_token_id=generator.tokenizer.eos_token_id,
        )
        text = output[0]["generated_text"]
        cleaned = _clean_generated_text(text, prompt)
        cleaned = cleaned.strip('"').strip()

        if len(cleaned) < 15:
            continue
        if not cleaned.endswith(("?", ".", "!")):
            cleaned += "?"
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        starters.append(cleaned)

    # Fallback templates guarantee we always return the requested count even
    # if GPT-2 sampling produces too many near-duplicates/short outputs.
    fallback_templates = [
        "What first got you interested in {theme}?",
        "I'd love to hear your take on where {theme} is heading next.",
        "What's a project involving {theme} that you're excited about right now?",
        "How did you get started working with {theme}?",
    ]
    idx = 0
    while len(starters) < num_starters and idx < len(fallback_templates):
        candidate = fallback_templates[idx].format(theme=themes[0] if themes else "this space")
        if candidate.lower() not in seen:
            starters.append(candidate)
            seen.add(candidate.lower())
        idx += 1

    return starters[:num_starters]
