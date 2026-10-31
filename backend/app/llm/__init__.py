"""Zipshield LLM module: automated claim analysis via OpenRouter (vision model).

Public entry point:
    from app.llm.service import analyze_claim
    fields = analyze_claim(db, claim)   # dict with the 10 fields ready to persist

The "brain" (prompts, output validation and anti-injection layer) is self-contained;
the input/output shell is adapted to the Zipshield backend.
"""
