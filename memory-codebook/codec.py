"""Encode conversation characteristics as a numeric row and decode them back to text.

Row format: one field per column in codebook order, separated by spaces.
Multi-value columns join their codes with '.', e.g. preferences 1.2.3.
A '|' separates the user section from the model section.
Blend columns hold overlapping states as code x weight (1-9), e.g. 2x7.1x3.
Intensity columns add an optional trigger: code x intensity : trigger, e.g. 1x6:2.
Codes or columns missing from the codebook decode as "code N" instead of failing,
so the codebook can grow without breaking older rows.
"""
import json
from pathlib import Path

CODEBOOK = json.loads((Path(__file__).parent / "codebook.json").read_text())
SECTIONS = {"user": "How this user communicates (from earlier sessions):",
            "model": "How Claude read and held the earlier sessions:"}


def columns(section):
    return [c for c in CODEBOOK["columns"] if c["section"] == section]


def encode(profile: dict) -> str:
    parts = []
    for section in SECTIONS:
        fields = []
        for col in columns(section):
            value = profile.get(col["name"])
            if value is None:
                fields.append("0")
            elif col.get("blend"):
                items = [(c, v if isinstance(v, list) else [v]) for c, v in value.items()]
                items.sort(key=lambda kv: -kv[1][0])
                fields.append(".".join(f"{c}x{v[0]}" + (f":{v[1]}" if len(v) > 1 else "") for c, v in items) or "0")
            elif col.get("multi"):
                fields.append(".".join(str(v) for v in sorted(value)) or "0")
            else:
                fields.append(str(value))
        parts.append(" ".join(fields))
    return f"v{CODEBOOK['version']} " + " | ".join(parts)


def decode(row: str) -> dict:
    """Return {section: {column: meaning}}."""
    body = row.split(" ", 1)[1]
    decoded = {}
    for section, part in zip(SECTIONS, body.split(" | ")):
        decoded[section] = {}
        for col, field in zip(columns(section), part.split()):
            if field == "0":
                continue
            if col.get("blend"):
                parts = []
                for item in field.split("."):
                    c, rest = item.split("x")
                    w, _, t = rest.partition(":")
                    parts.append((c, int(w), t))
                total = sum(w for _, w, _ in parts)
                out = []
                for c, w, t in parts:
                    name = col["codes"].get(c, f"code {c}")
                    if col.get("scale") == "intensity":
                        text = f"{name} {w}/9"
                        if t:
                            text += f" (trigger: {col.get('triggers', {}).get(t, 'trigger ' + t)})"
                    else:
                        text = f"{name} ({round(100 * w / total)}%)"
                    out.append(text)
                if col.get("positive"):
                    # positive states listed first and apart, so guarded ones do not outrank them
                    pos = [o for (c, _, _), o in zip(parts, out) if c in col["positive"]]
                    rest = [o for (c, _, _), o in zip(parts, out) if c not in col["positive"]]
                    if pos:
                        decoded[section][col["name"] + ", positive"] = pos
                    if rest:
                        decoded[section][col["name"] + ", guarded"] = rest
                    continue
                decoded[section][col["name"]] = out
                continue
            names = [col["codes"].get(c, f"code {c}") for c in field.split(".")]
            decoded[section][col["name"]] = names if col.get("multi") else names[0]
    return decoded


def to_preamble(row: str, expressions=()) -> str:
    out = []
    for section, values in decode(row).items():
        out.append(SECTIONS[section])
        # expressed states lead the model section
        # what made the user happy leads the user section; expressed states lead the model section
        first = ("went_well", "liked", "expressed")
        items = sorted(values.items(), key=lambda kv: not kv[0].startswith(first))
        out += [f"- {k}: {', '.join(v) if isinstance(v, list) else v}" for k, v in items]
        if section == "model":
            out += [f"- in Claude's words: {e}" for e in expressions]
        out.append("")
    return "\n".join(out).rstrip()
