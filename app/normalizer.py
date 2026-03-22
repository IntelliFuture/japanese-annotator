"""Lightweight Japanese text normalizer.

Based on a safe subset of neologd normalization rules:
https://github.com/neologd/mecab-ipadic-neologd/wiki/Regexp
"""

from __future__ import annotations

import re
import unicodedata

_HYPHEN_RE = re.compile("[˗֊‐‑‒–⁃⁻₋−]+")
_LONG_VOWEL_RE = re.compile("[﹣－ｰ—―─━]+")
_TILDE_RE = re.compile("[~∼∾〜〰～]+")
_MULTI_SPACE_RE = re.compile(r" {2,}")
_CJK_SPACE_RE = re.compile(
    r"([\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3400-\u4DBF])"
    r" +"
    r"([\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3400-\u4DBF])"
)


def normalize(text: str) -> str:
    """Apply lightweight normalization to Japanese text."""
    text = text.strip()
    if not text:
        return text

    # 1. NFKC for half-width katakana → full-width, full-width alphanum → half-width
    text = unicodedata.normalize("NFKC", text)

    # 2. Hyphen-like characters → standard hyphen (U+002D)
    text = _HYPHEN_RE.sub("-", text)

    # 3. Long vowel marks → ー
    text = _LONG_VOWEL_RE.sub("ー", text)

    # 4. Remove tilde variants
    text = _TILDE_RE.sub("", text)

    # 5. Full-width space → half-width
    text = text.replace("\u3000", " ")

    # 6. Collapse multiple spaces
    text = _MULTI_SPACE_RE.sub(" ", text)

    # 7. Remove spaces between CJK characters
    text = _CJK_SPACE_RE.sub(r"\1\2", text)

    return text.strip()
