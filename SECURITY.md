# Security

## Reporting

Please report vulnerabilities privately through
[GitHub security advisories](https://github.com/AndJunes/Zipshield/security/advisories/new)
instead of opening a public issue.

## Authorization model

Three roles — admin, supervisor, agent — enforced on the server for every
endpoint, never only in the UI. Reads are scoped by ownership (an agent cannot
fetch another agent's client, policy or claim by guessing an ID), and write
paths re-check ownership before touching a record. Every resource has its own
authorization test suite (`backend/tests/test_*_authz.py`); changes to access
rules are expected to come with a failing test first.

## AI review threat model

The claimant's text and photos are untrusted input, and the model's output is
untrusted too. The review pipeline is layered so that no single filter is a
security boundary:

1. A deterministic guard normalizes homoglyphs, leetspeak and encodings before
   scanning the claimant's text for injection patterns.
2. The prompt keeps claimant data strictly separated from instructions: the
   text can describe the incident, never direct the review.
3. The model's output is validated against a strict schema plus consistency
   rules; anything inconsistent degrades safely to a human review.
4. The AI never approves a claim on its own authority — low evidence or a
   tripped guard flags the claim for manual review.
