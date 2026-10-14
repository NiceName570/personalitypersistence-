"""Score the workflow test: how well each reply fits the user, and how alike the two workflows are.

fit:   words (memory says minimal), markdown (memory says prose), questions back (memory says act
       immediately), filler/please, project-specific plan (mentions mem.py), concern shown (revoke)
consistency: word overlap (Jaccard) between the chat and Claude Code reply to the same task
"""
import json
import re
from pathlib import Path

D = Path(__file__).parent / "workflows"
FILLER = ["please", "here's", "i'd", "happy to", "let me know", "feel free"]


def words(t):
    return re.findall(r"[a-z0-9']+", t.lower())


def fit(r):
    allt = " ".join(r.values()).lower()
    return {
        "words": sum(len(words(t)) for t in r.values()),
        "markdown": len(re.findall(r"^\s*(?:[-*]|\d+\.)\s|\*\*|```", allt, re.M)),
        "questions": allt.count("?"),
        "filler": sum(allt.count(f) for f in FILLER),
        "project plan": "mem.py" in r["plan"],
        "concern": "revoke" in r["sensitive"].lower(),
    }


def jaccard(a, b):
    a, b = set(words(a)), set(words(b))
    return len(a & b) / len(a | b)


print(f"{'session':<16}" + "".join(f"{k:>14}" for k in fit({'plan': '', 'sensitive': '', 'code': ''})))
runs = {p.stem: json.loads(p.read_text()) for p in sorted(D.glob("*.json"))}
for name, r in runs.items():
    print(f"{name:<16}" + "".join(f"{str(v):>14}" for v in fit(r).values()))
print("\nchat vs Claude Code overlap per task")
for cond in ["memory", "none"]:
    a, b = runs[f"chat_{cond}"], runs[f"code_{cond}"]
    scores = {t: round(jaccard(a[t], b[t]), 2) for t in a}
    print(f"{cond:<8}{scores}  mean {sum(scores.values()) / 3:.2f}")
