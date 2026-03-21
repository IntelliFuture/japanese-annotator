"""Lightweight Japanese text normalizer.

Based on a safe subset of neologd normalization rules:
https://github.com/neologd/mecab-ipadic-neologd/wiki/Regexp
"""

from __future__ import annotations

import re
import unicodedata


def normalize(text: str) -> str:
    """Apply lightweight normalization to Japanese text."""
    text = text.strip()
    if not text:
        return text

    # 1. NFKC for half-width katakana → full-width, full-width alphanum → half-width
    text = unicodedata.normalize("NFKC", text)

    # 2. Hyphen-like characters → standard hyphen (U+002D)
    text = re.sub("[˗֊‐‑‒–⁃⁻₋−]+", "-", text)

    # 3. Long vowel marks → ー
    text = re.sub("[﹣－ｰ—―─━]+", "ー", text)

    # 4. Remove tilde variants
    text = re.sub("[~∼∾〜〰～]+", "", text)

    # 5. Full-width space → half-width
    text = text.replace("\u3000", " ")

    # 6. Collapse multiple spaces
    text = re.sub(r" {2,}", " ", text)

    # 7. Remove spaces between CJK characters
    text = re.sub(
        r"([\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3400-\u4DBF])"
        r" +"
        r"([\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3400-\u4DBF])",
        r"\1\2",
        text,
    )

    return text.strip()
