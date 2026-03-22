"""
Input sanitization utilities for production security.

Provides functions to strip HTML tags, control characters, and other
potentially dangerous content from user-supplied strings.
"""

import re
import unicodedata


# Matches HTML/XML tags including self-closing tags and script/style blocks
_HTML_TAG_RE = re.compile(r"<[^>]+>", re.DOTALL)

# Matches common HTML entities
_HTML_ENTITY_RE = re.compile(r"&(?:#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);")


def sanitize_string(value: str) -> str:
    """
    Sanitize a user-supplied string by removing HTML tags and control characters.

    This function:
    - Strips leading/trailing whitespace
    - Removes all HTML/XML tags
    - Removes HTML entities (e.g. &amp;, &#60;)
    - Removes ASCII control characters (except newline, carriage return, tab)
    - Normalizes Unicode to NFC form to prevent homoglyph-based bypasses

    Args:
        value: The raw string to sanitize.

    Returns:
        The sanitized string.
    """
    if not isinstance(value, str):
        return value

    # Strip leading/trailing whitespace
    value = value.strip()

    # Normalize Unicode
    value = unicodedata.normalize("NFC", value)

    # Remove HTML/XML tags
    value = _HTML_TAG_RE.sub("", value)

    # Remove HTML entities
    value = _HTML_ENTITY_RE.sub("", value)

    # Remove ASCII control characters (keep \t, \n, \r)
    value = "".join(
        ch for ch in value
        if ch in ("\t", "\n", "\r") or (ord(ch) >= 32) or (ord(ch) > 127)
    )

    # Collapse any resulting multiple spaces into one
    value = re.sub(r"  +", " ", value)

    return value.strip()


def validate_no_path_traversal(value: str, label: str = "value") -> str:
    """
    Validate that a string does not contain path traversal sequences.

    Raises ValueError if the value contains '..' , '/', '\\', or null bytes.

    Args:
        value: The string to validate (e.g. a job_id or filename).
        label: A human-readable label for error messages.

    Returns:
        The validated string.
    """
    dangerous_patterns = ("..", "/", "\\", "\x00")
    for pattern in dangerous_patterns:
        if pattern in value:
            raise ValueError(
                f"Invalid {label}: contains forbidden character sequence "
                f"{pattern!r}"
            )
    return value
