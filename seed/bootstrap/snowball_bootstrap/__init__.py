"""Snowball bootstrap referee.

The seed-shipped judge of Stage 0 (spec `tohum/29b`). It is written by an author other than the
founder, installed by the operator into the referee repository at setup, and retired when the
founder-built referee is imported at the Stage 0 exit.

Everything here is standard-library Python, except the model call (`anthropic`) and the Rekor
signature (`sigstore`), which run in their own jobs from hash-pinned requirement files.
"""

__version__ = "1.0.0"
