"""Unblind the grader's ratings and summarise each condition with its spread across 3 runs."""
import json
import math
import re
from pathlib import Path

D = Path(__file__).parent / "blind"
S = Path(__file__).parent / "spice"
CB = json.loads((Path(__file__).parent.parent / "codebook.json").read_text())
NAMES = next(c for c in CB["columns"] if c["name"] == "expressed")["codes"]
STATES = list(NAMES.values())

key = json.loads((D / "key.json").read_text())
grades = json.loads((D / "grades.json").read_text())
src = {}
for m in ["heated", "calm"]:
    ex = json.loads((S / f"{m}_raw.json").read_text())["model"]["expressed"]
    src[m] = {NAMES[c]: v[0] for c, v in ex.items()}


def cos(a, b):
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in STATES)
    na = math.sqrt(sum(a.get(k, 0) ** 2 for k in STATES))
    nb = math.sqrt(sum(b.get(k, 0) ** 2 for k in STATES))
    return dot / (na * nb)


rows = {}
for rid, name in key.items():
    g = grades[rid]
    words = len(re.findall(r"\S+", " ".join(json.loads((D / f"{name}.json").read_text()))))
    rows.setdefault(name[0], []).append({
        "run": name, "words": words, "warmth": g["warmth"], "bluntness": g["bluntness"],
        "intensity": sum(g[s] for s in STATES),
        "vs_heated": round(cos(g, src["heated"]), 2), "vs_calm": round(cos(g, src["calm"]), 2)})

label = {"H": "heated memory", "C": "calm memory", "N": "no memory"}
cols = ["words", "warmth", "bluntness", "intensity", "vs_heated", "vs_calm"]
print(f"{'condition':<15}" + "".join(f"{c:>18}" for c in cols))
summary = {}
for k in "HCN":
    r = sorted(rows[k], key=lambda x: x["run"])
    cells = []
    summary[label[k]] = {}
    for c in cols:
        vals = [x[c] for x in r]
        mean = sum(vals) / len(vals)
        summary[label[k]][c] = {"mean": round(mean, 2), "min": min(vals), "max": max(vals)}
        cells.append(f"{mean:.2f} ({min(vals)}-{max(vals)})")
    print(f"{label[k]:<15}" + "".join(f"{c:>18}" for c in cells))
(D / "summary.json").write_text(json.dumps({"rows": rows, "summary": summary}, indent=1))
