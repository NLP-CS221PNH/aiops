"""Deterministic BM25, preserving the approved preview's technical tokens."""

from collections import Counter, defaultdict
import math
import re


STOP = frozenset(
    "a an and are as at be been by for from has have in into is it of on or "
    "that the their this to was were will with".split()
)
TOKENIZER_VERSION = "technical-preview-v1-sorted-query-terms"
CONTENT_POLICY = "section_heading+newline+text-v1"


def tokens(text):
    if not isinstance(text, str):
        raise ValueError("tokenizer input must be text")
    result = []
    for value in re.findall(r"[\w]+(?:[-.:/][\w]+)*", text.lower()):
        if value in STOP:
            continue
        result.append(value)
        parts = re.split(r"[-.:/]", value)
        if len(parts) > 1:
            result.extend(part for part in parts if len(part) > 1 and part not in STOP)
    return result


def canonical_content(chunk):
    """Accept the boundary's canonical content or construct it from source fields."""
    content = chunk.get("content")
    if "section_heading" in chunk and "text" in chunk:
        if not isinstance(chunk["section_heading"], str) or not isinstance(chunk["text"], str):
            raise ValueError("chunk heading and text must be strings")
        expected = chunk["section_heading"] + "\n" + chunk["text"]
        if content is not None and content != expected:
            raise ValueError("chunk content disagrees with heading+newline+text policy")
        return expected
    if not isinstance(content, str):
        raise ValueError("chunk requires canonical content or section_heading and text")
    return content


def validate_chunks(chunks, require_content=True):
    if not isinstance(chunks, (list, tuple)):
        raise ValueError("chunks must be a list or tuple")
    result, seen = [], set()
    for chunk in chunks:
        if not isinstance(chunk, dict):
            raise ValueError("each chunk must be an object")
        chunk_id = chunk.get("chunk_id")
        document_id = chunk.get("document_id", chunk.get("parent_document_id"))
        if not isinstance(chunk_id, str) or not chunk_id.strip():
            raise ValueError("chunk_id must be a nonempty string")
        if not isinstance(document_id, str) or not document_id.strip():
            raise ValueError("document_id must be a nonempty string")
        if chunk_id in seen:
            raise ValueError(f"duplicate chunk_id: {chunk_id}")
        seen.add(chunk_id)
        normalized = {"chunk_id": chunk_id, "document_id": document_id}
        if require_content:
            normalized["content"] = canonical_content(chunk)
        result.append(normalized)
    return result


def validate_depth(depth):
    if type(depth) is not int or depth < 0:
        raise ValueError("depth must be a nonnegative integer")


class BM25:
    def __init__(self, chunks, k1=1.2, b=0.75):
        if isinstance(k1, bool) or not isinstance(k1, (int, float)) or not math.isfinite(k1) or k1 <= 0:
            raise ValueError("k1 must be finite and positive")
        if isinstance(b, bool) or not isinstance(b, (int, float)) or not math.isfinite(b) or not 0 <= b <= 1:
            raise ValueError("b must be finite and between zero and one")
        self.chunks = validate_chunks(chunks)
        self.k1, self.b = k1, b
        self.tf = [Counter(tokens(chunk["content"])) for chunk in self.chunks]
        self.lengths = [sum(terms.values()) for terms in self.tf]
        self.avg = sum(self.lengths) / max(1, len(self.lengths))
        self.postings = defaultdict(list)
        for index, terms in enumerate(self.tf):
            for term, frequency in terms.items():
                self.postings[term].append((index, frequency))

    def search(self, query, depth=50):
        validate_depth(depth)
        query_terms = sorted(set(tokens(query)))
        scores = defaultdict(float)
        count = len(self.chunks)
        for term in query_terms:
            postings = self.postings.get(term, ())
            if not postings:
                continue
            idf = math.log(1 + (count - len(postings) + 0.5) / (len(postings) + 0.5))
            for index, frequency in postings:
                denominator = frequency + self.k1 * (
                    1 - self.b + self.b * self.lengths[index] / self.avg
                )
                if not math.isfinite(denominator) or denominator <= 0:
                    raise ValueError("BM25 parameters produced an invalid denominator")
                scores[index] += idf * frequency * (self.k1 + 1) / denominator
                if not math.isfinite(scores[index]):
                    raise ValueError("BM25 parameters produced a nonfinite score")
        ordered = sorted(scores, key=lambda index: (-scores[index], self.chunks[index]["chunk_id"]))[:depth]
        return [
            {"chunk_id": self.chunks[index]["chunk_id"],
             "document_id": self.chunks[index]["document_id"],
             "rank": rank, "score": scores[index]}
            for rank, index in enumerate(ordered, 1)
        ]
