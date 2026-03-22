from __future__ import annotations

import glob
import json
import logging
import os
import re
from html import escape

import sudachipy

from app.models import AnnotateResponse, TokenResult

logger = logging.getLogger(__name__)

_SPLIT_MODE = {
    "A": sudachipy.SplitMode.A,
    "B": sudachipy.SplitMode.B,
    "C": sudachipy.SplitMode.C,
}

# Unicode ranges
_KATAKANA_START = 0x30A1  # ァ
_KATAKANA_END = 0x30F4    # ヴ (ヵ/ヶ beyond this have no simple hiragana mapping)
_CJK_START = 0x4E00       # CJK Unified Ideographs
_CJK_END = 0x9FFF
_CJK_EXT_A_START = 0x3400  # CJK Extension A
_CJK_EXT_A_END = 0x4DBF

_KATA_TO_HIRA_OFFSET = ord("ぁ") - ord("ァ")

_KATA_HIRA_TABLE = str.maketrans(
    "".join(chr(c) for c in range(_KATAKANA_START, _KATAKANA_END + 1)),
    "".join(chr(c + _KATA_TO_HIRA_OFFSET) for c in range(_KATAKANA_START, _KATAKANA_END + 1)),
)

USER_DICT_DIR = os.environ.get("USER_DICT_DIR", "user_dict")


def _kata_to_hira(text: str) -> str:
    """Convert katakana to hiragana."""
    return text.translate(_KATA_HIRA_TABLE)


def _contains_kanji(text: str) -> bool:
    """Check if text contains any CJK Unified Ideographs or Extension A kanji."""
    return any(
        _CJK_START <= ord(ch) <= _CJK_END or _CJK_EXT_A_START <= ord(ch) <= _CJK_EXT_A_END
        for ch in text
    )


# Regex to split surface into alternating kanji/kana segments.
_KANA_SPLIT_RE = re.compile(r'([\u3041-\u3096\u30A1-\u30FC]+)')


def _split_furigana(surface: str, reading: str) -> list[tuple[str, str | None]]:
    """Split surface into (text, reading|None) pairs, assigning reading only to kanji parts.

    Algorithm:
      1. If no kanji, return the whole surface with no reading.
      2. If pure kanji (single segment), return with the full reading.
      3. For mixed kanji/kana, split surface into segments via _KANA_SPLIT_RE,
         then walk through them with a ``remaining`` reading buffer:
         - Kana segment: find its hiragana form in ``remaining`` and advance past it.
         - Kanji segment: look ahead for the next kana boundary, slice ``remaining``
           up to that boundary as the kanji's reading.

    Example: 食べる (たべる)
      segments = ['食', 'べる']
      '食' (kanji) → next kana 'べる', remaining='たべる' → reading before 'べる' is 'た'
      'べる' (kana) → no reading needed
      Result: [('食', 'た'), ('べる', None)]
    """
    if not _contains_kanji(surface):
        return [(surface, None)]

    segments = [s for s in _KANA_SPLIT_RE.split(surface) if s]
    if len(segments) == 1:
        return [(surface, reading)]

    result: list[tuple[str, str | None]] = []
    remaining = reading

    for seg_idx, seg in enumerate(segments):
        if not _contains_kanji(seg):
            # Kana segment — find and consume matching portion from remaining reading
            seg_hira = _kata_to_hira(seg)
            idx = remaining.find(seg_hira)
            if idx != -1:
                remaining = remaining[idx + len(seg_hira):]
            result.append((seg, None))
        else:
            # Kanji segment — look ahead for next kana to determine reading boundary
            next_kana_hira = None
            for look in range(seg_idx + 1, len(segments)):
                if not _contains_kanji(segments[look]):
                    next_kana_hira = _kata_to_hira(segments[look])
                    break

            if next_kana_hira:
                idx = remaining.find(next_kana_hira)
                if idx != -1:
                    result.append((seg, remaining[:idx]))
                    remaining = remaining[idx:]
                else:
                    # Fallback: assign all remaining reading to this kanji
                    result.append((seg, remaining))
                    remaining = ""
            else:
                # Last segment is kanji — all remaining reading belongs to it
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
            logger.info("Loading user dictionaries: %s", user_dicts)
        dic = sudachipy.Dictionary(dict="full", config=config)
        self._tokenizer = dic.create()
        logger.info("Tokenizer loaded successfully")

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
