"""Secret patterns checked before any text leaves for the model provider (`tohum/08` 11)."""

from __future__ import annotations

import re

_L = r"(?<![A-Za-z0-9])"  # for the prefixes that are common inside words (sk-, AIza, eyJ ...): not glued to a letter or digit

PATTERNS: dict[str, re.Pattern[str]] = {
    "private_key": re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY(?: BLOCK)?-----"),
    "github_token": re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}"),
    "github_pat": re.compile(r"github_pat_[A-Za-z0-9_]{60,}"),
    "anthropic_key": re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    "aws_access_key": re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[0-9A-Z]{16}(?![A-Za-z0-9])"),
    "slack_token": re.compile(r"xox[abprs]-[A-Za-z0-9-]{10,}"),
    "openai_key": re.compile(_L + r"sk-(?!ant-)(?:proj-|svcacct-)?[A-Za-z0-9_\-]{32,}"),
    "stripe_key": re.compile(_L + r"[sr]k_(?:live|test)_[A-Za-z0-9]{16,}"),
    "google_api_key": re.compile(_L + r"AIza[0-9A-Za-z_\-]{35}"),
    "npm_token": re.compile(r"npm_[A-Za-z0-9]{36}(?![A-Za-z0-9])"),
    "jwt": re.compile(_L + r"eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"),
    # A credential-like name (GITHUB_TOKEN, db_password, aws_secret_access_key ...) assigned a quoted value ...
    "generic_assignment": re.compile(
        r"(?i)[A-Za-z0-9_]*(?:api[_-]?key|secret|password|passwd|token)[A-Za-z0-9_]*\s*[:=]\s*['\"]"
        r"[A-Za-z0-9/+_\-]{24,}['\"]"
    ),
    # ... or an unquoted value that looks random: letters of both cases and a digit (a snake_case identifier,
    # a plain number or a lower-case word does not), or a long hex string.
    "generic_assignment_bare": re.compile(
        r"(?i)[A-Za-z0-9_]*(?:api[_-]?key|secret|password|passwd|token)[A-Za-z0-9_]*\s*[:=]\s*"
        r"(?:(?-i:(?=[A-Za-z0-9/+_\-]*[a-z])(?=[A-Za-z0-9/+_\-]*[A-Z])(?=[A-Za-z0-9/+_\-]*[0-9])"
        r"[A-Za-z0-9/+_\-]{20,})|[0-9a-f]{32,})(?![A-Za-z0-9/+_\-])"
    ),
}


def scan(text: str) -> list[str]:
    """Return the names of the patterns that match ``text``."""
    return sorted(name for name, pattern in PATTERNS.items() if pattern.search(text))
