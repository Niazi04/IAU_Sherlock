import re
import unicodedata

_BIDI_RE = re.compile(
    r"[\u200b\u200e\u200f"
    r"\u202a\u202b\u202c\u202d\u202e"
    r"\u2066\u2067\u2068\u2069"
    r"\ufeff]"
)

_CHAR_MAP = str.maketrans({
    "\u064A": "\u06CC",   # Arabic ي → Farsi ی
    "\u0643": "\u06A9",   # Arabic ك → Farsi ک
    "\u0629": "\u0647",   # Arabic ة → ه
    "\u0649": "\u06CC",   # Arabic ى → Farsi ی
    "\u06C0": "\u0647",   # ۀ → ه
    "\u0671": "\u0627",   # ٱ → ا
    "\u200D": "",         # ZWJ — remove
})


def strip_bidi(text: str) -> str:
    return _BIDI_RE.sub("", text)


def normalise_farsi_chars(text: str) -> str:
    text = _BIDI_RE.sub("", text)
    text = text.translate(_CHAR_MAP)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = unicodedata.normalize("NFC", text)
    return text