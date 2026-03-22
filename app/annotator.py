from __future__ import annotations

import glob
import json
import os
import re
from html import escape

import sudachipy

from app.models import AnnotateResponse, TokenResult

_SPLIT_MODE = {
    "A": sudachipy.SplitMode.A,
    "B": sudachipy.SplitMode.B,
    "C": sudachipy.SplitMode.C,
}

_KATA_TO_HIRA_OFFSET = ord("ぁ") - ord("ァ")

USER_DICT_DIR = os.environ.get("USER_DICT_DIR", "user_dict")


def _kata_to_hira(text: str) -> str:
    """Convert katakana to hiragana."""
    result: list[str] = []
    for ch in text:
        cp = ord(ch)
        # Safe katakana range: U+30A1 (ァ) to U+30F4 (ヴ).
        # Characters beyond ヴ (e.g. ヵ U+30F5, ヶ U+30F6) do not have
        # direct hiragana equivalents at a simple codepoint offset, so
        # they are left unchanged.
        if 0x30A1 <= cp <= 0x30F4:
            result.append(chr(cp + _KATA_TO_HIRA_OFFSET))
        else:
            result.append(ch)
    return "".join(result)


def _contains_kanji(text: str) -> bool:
    """Check if text contains any CJK Unified Ideographs (kanji)."""
    return any(0x4E00 <= ord(ch) <= 0x9FFF or 0x3400 <= ord(ch) <= 0x4DBF for ch in text)


# Regex to split surface into alternating kanji/kana segments.
_KANA_SPLIT_RE = re.compile(r'([\u3041-\u3096\u30A1-\u30FC]+)')


def _split_furigana(surface: str, reading: str) -> list[tuple[str, str | None]]:
    """Split surface into (text, reading|None) pairs, assigning reading only to kanji parts.

    Example: 食べる (たべる) → [('食', 'た'), ('べる', None)]
    """
    if not _contains_kanji(surface):
        return [(surface, None)]

    segments = [s for s in _KANA_SPLIT_RE.split(surface) if s]
    if len(segments) == 1:
        # Pure kanji — whole reading applies
        return [(surface, reading)]

    result: list[tuple[str, str | None]] = []
    remaining = reading

    for i, seg in enumerate(segments):
        if not _contains_kanji(seg):
            # Kana segment — consume matching part from remaining reading
            seg_hira = _kata_to_hira(seg)
            idx = remaining.find(seg_hira)
            if idx != -1:
                remaining = remaining[idx + len(seg_hira):]
            result.append((seg, None))
        else:
            # Kanji segment — find next kana boundary to determine its reading
            next_kana_hira = None
            for j in range(i + 1, len(segments)):
                if not _contains_kanji(segments[j]):
                    next_kana_hira = _kata_to_hira(segments[j])
                    break

            if next_kana_hira:
                idx = remaining.find(next_kana_hira)
                if idx != -1:
                    result.append((seg, remaining[:idx]))
                    remaining = remaining[idx:]
                else:
                    result.append((seg, remaining))
                    remaining = ""
            else:
                # Last segment is kanji — all remaining reading is for it
                result.append((seg, remaining))
                remaining = ""

    return result


def _find_user_dicts() -> list[str]:
    """Find all .dic files in the user dict directory."""
    pattern = os.path.join(USER_DICT_DIR, "*.dic")
    return sorted(glob.glob(pattern))


class Annotator:
    def __init__(self) -> None:
        self._tokenizer: sudachipy.Tokenizer
        self._load_tokenizer()

    def _load_tokenizer(self) -> None:
        user_dicts = _find_user_dicts()
        config = None
        if user_dicts:
            config = json.dumps({"userDict": user_dicts})
        dic = sudachipy.Dictionary(dict="full", config=config)
        self._tokenizer = dic.create()

    def reload_dict(self) -> None:
        """Reload tokenizer with updated user dictionaries."""
        self._load_tokenizer()

    def annotate(self, text: str, mode: str = "C") -> AnnotateResponse:
        split_mode = _SPLIT_MODE.get(mode.upper(), sudachipy.SplitMode.C)
        morphemes = self._tokenizer.tokenize(text, split_mode)

        tokens: list[TokenResult] = []
        ruby_parts: list[str] = []

        for m in morphemes:
            surface = m.surface()
            reading_hira = _kata_to_hira(m.reading_form())
            lemma = m.normalized_form()
            pos = m.part_of_speech()[0]

            tokens.append(TokenResult(
                surface=surface,
                reading=reading_hira,
                lemma=lemma,
                pos=pos,
            ))

            for seg_text, seg_reading in _split_furigana(surface, reading_hira):
                if seg_reading is not None:
                    ruby_parts.append(
                        f"<ruby>{escape(seg_text)}<rt>{escape(seg_reading)}</rt></ruby>"
                    )
                else:
                    ruby_parts.append(escape(seg_text))

        return AnnotateResponse(tokens=tokens, ruby_html="".join(ruby_parts))
