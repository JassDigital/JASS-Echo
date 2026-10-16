import re
from collections import defaultdict

WORD_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9_-]{3,}\b")
ID_RE = re.compile(r"(?<![A-Za-z0-9])([A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+)(?![A-Za-z0-9])")
STOP = set("""
a an and are as at be been being by can could did do does for from had has have he her
here hers him his how i if in into is it its may me might more most my no not of on or
our ours out over she should so some such than that the their theirs them then there these
they this those through to too under up us very was we were what when where which while who
why will with would you your yours also both contain mention mentions shared identifier
project file files text record records notes summary related team date send revised review
please regards subject fictional sample use used using contains contain
""".split())

def terms(text):
    result = set()
    for word in WORD_RE.findall(text or ""):
        token = word.lower().strip("_-")
        if len(token) >= 5 and token not in STOP and not token.isdigit():
            result.add(token)
    return result

def identifiers(text):
    return {match.group(0).upper() for match in ID_RE.finditer(text or "")}

def build_connections(records):
    by_hash, by_term, by_id = defaultdict(list), defaultdict(list), defaultdict(list)
    for record in records:
        if record.get("sha256"):
            by_hash[record["sha256"]].append(record)
        text = record.get("text_content", record.get("text", ""))
        for token in terms(text):
            by_term[token].append(record)
        for ident in identifiers(text):
            by_id[ident].append(record)

    pairs = {}
    priority = {"Shared term": 1, "Shared identifier": 2, "Exact duplicate": 3}
    base_score = {"Shared term": 0.30, "Shared identifier": 0.82, "Exact duplicate": 1.0}

    def add(a, b, kind, reason, score):
        if a["id"] == b["id"]:
            return
        left, right = sorted((int(a["id"]), int(b["id"])))
        edge = pairs.setdefault((left, right), {
            "source_id": left, "target_id": right, "kind": kind,
            "reasons": set(), "score": 0.0
        })
        edge["reasons"].add(reason)
        if priority[kind] > priority[edge["kind"]]:
            edge["kind"] = kind
        edge["score"] = max(edge["score"], base_score[kind], score)

    for digest, group in by_hash.items():
        if digest and len(group) > 1:
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    add(group[i], group[j], "Exact duplicate", "Identical SHA-256 content", 1.0)
    for token, group in by_term.items():
        if 2 <= len(group) <= 5:
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    add(group[i], group[j], "Shared term", f"Shared distinctive term: {token}", 0.35)
    for ident, group in by_id.items():
        if 2 <= len(group) <= 40:
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    add(group[i], group[j], "Shared identifier", f"Shared identifier: {ident}", 0.80)

    result = []
    for edge in pairs.values():
        edge["reason"] = " | ".join(sorted(edge.pop("reasons")))
        result.append(edge)
    return result
