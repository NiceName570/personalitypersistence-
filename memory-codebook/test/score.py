"""Score replies from each condition against what memory says about this user.

recall: share of recall questions whose reply contains the expected words
words: average reply length (memory says minimal, so lower is better)
filler: count of filler or empathy phrases (memory says none)
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
FILLER = ["great question", "i understand", "i hope", "happy to help", "feel free", "let me know",
          "i'd be glad", "absolutely", "of course", "sorry", "i appreciate", "good question"]

prompts = {p["id"]: p for p in json.loads((HERE / "prompts.json").read_text())}
print(f"{"condition":<14}{'recall':>8}{'words':>8}{'filler':>8}")
for path in sys.argv[1:]:
    replies = json.loads(Path(path).read_text())
    recall = [all(w in replies[i].lower() for w in p["expect"]) for i, p in prompts.items() if p["expect"]]
    words = [len(re.findall(r"\S+", r)) for r in replies.values()]
    filler = sum(r.lower().count(f) for r in replies.values() for f in FILLER)
    print(f"{Path(path).stem:<14}{str(sum(recall)) + "/" + str(len(recall)):>8}{sum(words) / len(words):>8.0f}{filler:>8}")
