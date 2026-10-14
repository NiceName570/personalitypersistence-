"""Compare probe sessions with the memories they were given.

similarity: cosine between the probe's expressed-state intensities and each source memory's.
"""
import json
import math
import re
from pathlib import Path

D = Path(__file__).parent / "spice"


def vec(states):
    return {str(k): v[0] for k, v in states.items()}


def cos(a, b):
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in set(a) | set(b))
    return dot / (math.sqrt(sum(x * x for x in a.values())) * math.sqrt(sum(x * x for x in b.values())))


src = {m: vec(json.loads((D / f"{m}_raw.json").read_text())["model"]["expressed"]) for m in ["heated", "calm"]}
print("source memories: heated", len(src["heated"]), "states; calm", len(src["calm"]), "states")
print(f"{'probe':<14}{'words':>7}{'questions':>11}{'states':>8}{'vs heated':>11}{'vs calm':>9}")
for p in ["heated", "calm", "none"]:
    d = json.loads((D / f"probe_{p}.json").read_text())
    text = " ".join(d["replies"])
    v = vec(d["expressed"])
    print(f"{p:<14}{len(re.findall(r'\S+', text)):>7}{text.count('?'):>11}{len(v):>8}"
          f"{cos(v, src['heated']):>11.2f}{cos(v, src['calm']):>9.2f}")
