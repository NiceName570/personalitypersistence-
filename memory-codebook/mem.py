"""Our own memory store: no API, no dependencies.

  python3 mem.py add session.json     merge one session's extraction into memory
  python3 mem.py load [question]      print text to paste at the start of a new chat
  python3 mem.py history              show each session's numeric row
  python3 mem.py export DIR           write the same memory for every workflow into DIR:
                                      chat.txt (paste into a new chat), CLAUDE.md (Claude Code),
                                      project_instructions.txt (a Claude Project)

session.json is what extract_prompt.md returns:
  {"profile": {...}, "model": {...}, "expression": "...", "facts": [...]}
"""
import json
import math
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from codec import CODEBOOK, encode, to_preamble

import os
STORE = Path(os.environ.get("MEM_STORE", Path(__file__).parent / "store.json"))
STOP = set("a an and are as at be by for from has have in is it of on or that the this to was were with".split())


def load_store():
    if STORE.exists():
        return json.loads(STORE.read_text())
    return {"sessions": [], "facts": []}


def words(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


def similar(a, b):
    wa, wb = set(words(a)), set(words(b))
    return len(wa & wb) / max(len(wa | wb), 1)


NEG = CODEBOOK.get("negative", {})
WEIGHTS = CODEBOOK.get("weights", {})


def weight(column, code):
    """Positive codes count more, guarded ones less, hedging and urgency least (codebook "weights")."""
    return WEIGHTS.get(column, {}).get(str(code), 1)


def merged_profile(sessions):
    """Single columns take the most common code across sessions; multi columns keep every code seen.
    Negative codes (codebook "negative") count for negative_weight of a positive one."""
    profile = {}
    for col in CODEBOOK["columns"]:
        name = col["name"]
        seen = [s["profile"][name] for s in sessions if name in s["profile"]]
        if not seen:
            continue
        if col.get("scale") == "intensity":
            # average intensity per state over the sessions that showed it; keep the latest trigger
            sums, counts, trig = Counter(), Counter(), {}
            for states in seen:
                for c, v in states.items():
                    v = v if isinstance(v, list) else [v]
                    sums[c] += v[0]
                    counts[c] += 1
                    if len(v) > 1:
                        trig[c] = v[1]
            profile[name] = {c: [min(9, max(1, round(weight(name, c) * sums[c] / counts[c])))] + ([trig[c]] if c in trig else []) for c in sums}
        elif col.get("blend"):
            # average each state's share across sessions, rescaled to weights 1-9
            totals = Counter()
            for weights in seen:
                norm = sum(weights.values())
                for c, w in weights.items():
                    totals[str(c)] += w / norm
            top = max(totals.values())
            profile[name] = {c: max(1, round(9 * t / top)) for c, t in totals.items()}
        elif col.get("multi"):
            profile[name] = sorted({c for codes in seen for c in codes})
        else:
            counts = Counter()
            for c in seen:
                counts[c] += weight(name, c)
            top = max(counts.values())
            # ties go to the most recent session
            profile[name] = next(c for c in reversed(seen) if counts[c] == top)
    return profile


def add(path):
    store = load_store()
    session = json.loads(Path(path).read_text())
    profile = {**session["profile"], **session.get("model", {})}
    store["sessions"].append({"date": date.today().isoformat(), "row": encode(profile),
                              "profile": profile, "expression": session.get("expression"),
                              "expressed_as": session.get("expressed_as", {}),
                              "went_well_as": session.get("went_well_as", {})})
    added = 0
    for fact in session.get("facts", []):
        match = next((f for f in store["facts"] if similar(f["text"], fact) >= 0.6), None)
        if match:
            match["text"], match["seen"] = fact, match["seen"] + 1
        else:
            store["facts"].append({"text": fact, "seen": 1})
            added += 1
    STORE.write_text(json.dumps(store, indent=2))
    print(f"Session {len(store['sessions'])} saved: {added} new facts, {len(store['facts'])} total.")


def rank(facts, question, limit=10):
    docs = [words(f["text"]) for f in facts]
    df = Counter(w for d in docs for w in set(d))
    q = words(question)
    scores = []
    for f, d in zip(facts, docs):
        tf = Counter(d)
        score = sum(tf[w] * math.log((1 + len(docs)) / (1 + df[w])) for w in q)
        scores.append((score, f["seen"], f))
    return [f for s, _, f in sorted(scores, key=lambda x: (-x[0], -x[1])) if s > 0][:limit]


def load(question=None):
    store = load_store()
    row = encode(merged_profile(store["sessions"]))
    facts = rank(store["facts"], question) if question else store["facts"]
    print(f"Memory row: {row}\n")
    good = {}
    for session in store["sessions"]:
        good.update(session.get("went_well_as", {}))
    profile = merged_profile(store["sessions"])
    liked = profile.get("liked", [])
    if good or liked:
        ww = next(c for c in CODEBOOK["columns"] if c["name"] == "went_well")["codes"]
        lk = next(c for c in CODEBOOK["columns"] if c["name"] == "liked")["codes"]
        print("What made this user happy. This matters most: do more of it, starting with the first reply.")
        for code, quote in good.items():
            print(f'- they were {ww.get(code, "code " + code)}: "{quote}"')
        for code in liked:
            print(f"- they liked: {lk.get(str(code), 'code ' + str(code))}")
        print()
    expressions = [s["expression"] for s in store["sessions"] if s.get("expression")][-3:]
    print(to_preamble(row, expressions))
    names = next(c for c in CODEBOOK["columns"] if c["name"] == "expressed")["codes"]
    quotes = {}
    for session in store["sessions"]:
        quotes.update(session.get("expressed_as", {}))
    states = merged_profile(store["sessions"]).get("expressed", {})
    col = next(c for c in CODEBOOK["columns"] if c["name"] == "expressed")
    keep = [(c, v[0] if isinstance(v, list) else v) for c, v in states.items()
            if col.get("carry", {}).get(c) and (v[0] if isinstance(v, list) else v) >= (2 if c in NEG.get("expressed", []) else 3)]
    if keep:
        print("\nQualities to carry into this session. Brief means short, not cold: keep these even in one-line replies.")
        for c, w in sorted(keep, key=lambda x: (x[0] not in col.get("positive", []), -x[1])):
            line = f"- {col['carry'][c]}"
            if c in quotes:
                line += f' Last time: "{quotes[c]}"'
            print(line)
    if quotes:
        print("\nHow those states showed in Claude's words:")
        for code, quote in sorted(quotes.items(), key=lambda kv: kv[0] not in col.get("positive", [])):
            print(f'- {names.get(code, "code " + code)}: "{quote}"')
    print("\nFacts from earlier sessions:")
    for f in facts:
        print(f"- {f['text']}")


HEADER = ("You are continuing as the same agent across workflows. Carry forward the user's style, "
          "the stance and expressed states below, and the facts, whatever the task is.\n\n")


def export(out_dir):
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        load()
    text = HEADER + buf.getvalue()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "chat.txt").write_text(text)
    (out / "project_instructions.txt").write_text(text)
    (out / "CLAUDE.md").write_text("# Agent memory\n\n" + text)
    print(f"Wrote chat.txt, CLAUDE.md and project_instructions.txt to {out}")


def replay():
    """Decompress stored sessions into alternating turns, so a new session runs through the conversation
    instead of reading a summary. Each turn keeps the words that carried that side's states."""
    store = load_store()
    turns = [t for s in store["sessions"] for t in s.get("replay", [])]
    for t in turns:
        print(f"User: {t['user']}")
        print(f"Claude: {t['claude']}\n")


def history():
    for i, s in enumerate(load_store()["sessions"], 1):
        print(f"{i}  {s['date']}  {s['row']}")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or ["load"]
    {"add": lambda: add(args[0]), "load": lambda: load(" ".join(args) or None), "history": history, "replay": replay,
     "export": lambda: export(args[0])}[cmd]()
