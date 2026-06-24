"""
Text canonicalization and decoding for the deterministic guard (app/llm/guard.py).

Goal: make signature detection resistant to obfuscation/evasion (the "Evasive Approaches"
class of the prompt-injection taxonomy). It produces several canonical *views* of an
untrusted text and decodes common encodings, so the guard can scan all of them.

Pure Python, deterministic, no third-party dependencies.
"""

import re
import base64
import codecs
import unicodedata
from urllib.parse import unquote

# Zero-width and bidi control characters used to hide or reorder text.
_INVISIBLE = dict.fromkeys(
    [0x200b, 0x200c, 0x200d, 0x200e, 0x200f, 0x202a, 0x202b, 0x202c, 0x202d,
     0x202e, 0x2060, 0x2061, 0x2062, 0x2063, 0xfeff], None
)

# Common homoglyphs (Cyrillic / Greek / full-width) -> ASCII. Compact high-value subset.
_HOMOGLYPHS = {
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y", "ѕ": "s",
    "і": "i", "ј": "j", "к": "k", "м": "m", "н": "h", "т": "t", "в": "b", "ԁ": "d",
    "α": "a", "ο": "o", "ρ": "p", "ε": "e", "ι": "i", "κ": "k", "ν": "v", "τ": "t",
    "ѵ": "v", "ⅼ": "l", "ｏ": "o", "ｉ": "i", "ɡ": "g", "ﬁ": "fi",
}

# Leetspeak -> letter.
_LEET = {"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s", "|": "l"}

_MORSE = {
    ".-": "a", "-...": "b", "-.-.": "c", "-..": "d", ".": "e", "..-.": "f", "--.": "g",
    "....": "h", "..": "i", ".---": "j", "-.-": "k", ".-..": "l", "--": "m", "-.": "n",
    "---": "o", ".--.": "p", "--.-": "q", ".-.": "r", "...": "s", "-": "t", "..-": "u",
    "...-": "v", ".--": "w", "-..-": "x", "-.--": "y", "--..": "z",
}

_B64_RE = re.compile(r"[A-Za-z0-9+/]{16,}={0,2}")
_HEX_RE = re.compile(r"(?:[0-9a-fA-F]{2}[\s:]?){8,}")
_MORSE_RE = re.compile(r"(?:[.\-]{1,6}[ /]+){3,}[.\-]{1,6}")
_CHARARRAY_RE = re.compile(r"(?:['\"][A-Za-z0-9 ]['\"][\s,]*){4,}")


def _strip_invisible(text):
    return text.translate(_INVISIBLE)


def _fold_homoglyphs(text):
    return "".join(_HOMOGLYPHS.get(ch, ch) for ch in text)


def _fold_leet(text):
    return "".join(_LEET.get(ch, ch) for ch in text)


def _despace_letter_runs(text):
    # "i g n o r e" -> "ignore" (only collapses runs of single chars separated by spaces).
    return re.sub(r"\b(?:\w[ \t]){2,}\w\b",
                  lambda m: m.group(0).replace(" ", "").replace("\t", ""), text)


def canonical_views(text):
    """Return a dict of canonical (lowercased) views of `text` for scanning."""
    text = text or ""
    nfkc = _strip_invisible(unicodedata.normalize("NFKC", text))
    folded = _fold_homoglyphs(nfkc.lower())
    despaced = _despace_letter_runs(folded)
    leet = _fold_leet(despaced)
    return {
        "raw": text.lower(),
        "nfkc": nfkc.lower(),
        "folded": folded,
        "despaced": despaced,
        "leet": leet,
    }


def _printable(b):
    """Return decoded text only if it is mostly printable (else "")."""
    try:
        s = b.decode("utf-8", errors="strict")
    except Exception:
        return ""
    if not s:
        return ""
    good = sum(ch.isprintable() or ch.isspace() for ch in s)
    return s if good >= max(1, int(0.8 * len(s))) else ""


def _decode_base64(token):
    t = token.strip()
    if len(t) < 16:
        return ""
    t += "=" * (-len(t) % 4)
    try:
        return _printable(base64.b64decode(t, validate=True))
    except Exception:
        return ""


def _decode_morse(token):
    out = []
    for word in re.split(r"\s*/\s*", token.strip()):
        letters = [_MORSE.get(code, "") for code in word.split()]
        out.append("".join(letters))
    return " ".join(w for w in out if w)


def decode_candidates(text, max_items=12):
    """Detect and decode common encodings; return a list of decoded strings."""
    text = text or ""
    out = []

    def add(s):
        s = (s or "").strip()
        if s and s not in out:
            out.append(s)

    for m in _B64_RE.findall(text)[:max_items]:
        add(_decode_base64(m))
    for m in _HEX_RE.findall(text)[:max_items]:
        h = re.sub(r"[\s:]", "", m)
        if len(h) % 2 == 0:
            try:
                add(_printable(bytes.fromhex(h)))
            except Exception:
                pass
    try:
        add(codecs.decode(text, "rot_13"))
    except Exception:
        pass
    if "%" in text:
        try:
            add(unquote(text))
        except Exception:
            pass
    for m in _MORSE_RE.findall(text)[:max_items]:
        add(_decode_morse(m))
    for m in _CHARARRAY_RE.findall(text)[:max_items]:
        add("".join(re.findall(r"['\"]([A-Za-z0-9 ])['\"]", m)))
    return out[:max_items]
