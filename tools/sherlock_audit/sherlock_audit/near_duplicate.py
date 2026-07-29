from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


def _tokenize(text: str) -> list[str]:
    # conservative tokenization; avoids extra deps.
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    toks = [t for t in text.split() if t]
    return toks


def _shingles(tokens: list[str], k: int = 5) -> list[str]:
    if len(tokens) < k:
        return [" ".join(tokens)] if tokens else []
    return [" ".join(tokens[i : i + k]) for i in range(0, len(tokens) - k + 1)]


def _hash64(s: str) -> int:
    h = hashlib.blake2b(s.encode("utf-8", errors="ignore"), digest_size=8).digest()
    return int.from_bytes(h, "big", signed=False)


def simhash(text: str, k_shingle: int = 5) -> int:
    """Compute 64-bit SimHash over k-word shingles."""
    toks = _tokenize(text)
    sh = _shingles(toks, k=k_shingle)
    if not sh:
        return 0

    # weight all shingles equally (v0)
    v = [0] * 64
    for s in sh:
        x = _hash64(s)
        for i in range(64):
            bit = (x >> i) & 1
            v[i] += 1 if bit else -1

    out = 0
    for i in range(64):
        if v[i] >= 0:
            out |= (1 << i)
    return out


def hamming64(a: int, b: int) -> int:
    x = a ^ b
    # python popcount
    return x.bit_count()


@dataclass(frozen=True)
class NearDupPair:
    url_a: str
    url_b: str
    hamming: int


def find_near_duplicates(url_to_text: dict[str, str], max_hamming: int = 6) -> list[NearDupPair]:
    """Brute-force near-duplicate detection via SimHash.

    Works for <=~500 pages; for larger runs we should add LSH.
    """
    items = [(u, simhash(t)) for u, t in url_to_text.items()]
    pairs: list[NearDupPair] = []

    for i in range(len(items)):
        u1, h1 = items[i]
        for j in range(i + 1, len(items)):
            u2, h2 = items[j]
            d = hamming64(h1, h2)
            if d <= max_hamming:
                pairs.append(NearDupPair(url_a=u1, url_b=u2, hamming=d))

    pairs.sort(key=lambda p: (p.hamming, p.url_a, p.url_b))
    return pairs
