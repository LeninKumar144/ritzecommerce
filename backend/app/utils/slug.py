"""URL slugs derived from names."""

import re


def slugify(value: str, max_length: int = 140) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    slug = slug[:max_length].strip("-")
    return slug or "item"
