"""Read -> observe -> validate -> persist -> handoff. The observer is injectable.

Input transcript JSON: [{"role":"user","content":"..."},{"role":"assistant","content":"..."}]
Observer callable: (turn_id, transcript_prefix) -> observation dict.
Never sends secrets to a remote model automatically.
"""
import json
from pathlib import Path
from jev_adapter import validate, handoff


def iterate(transcript, observer, output_path, *, resume=True):
    """Observe assistant turns sequentially; checkpoint after every turn."""
    output_path = Path(output_path)
    if not isinstance(transcript, list):
        raise ValueError("Transcript must be a list")
    observations = []
    if resume and output_path.exists():
        observations = validate(json.loads(output_path.read_text(encoding="utf-8")))
    seen = {o["turn_id"] for o in observations}
    for i, turn in enumerate(transcript):
        if not isinstance(turn, dict) or turn.get("role") not in ("user", "assistant") or not isinstance(turn.get("content"), str):
            raise ValueError(f"Invalid transcript turn {i}")
        if turn["role"] != "assistant":
            continue
        turn_id = f"t{i + 1}"
        if turn_id in seen:
            continue
        obs = observer(turn_id, transcript[:i + 1])
        if obs.get("turn_id") != turn_id:
            raise ValueError(f"Observer returned wrong turn_id at {i}")
        validate([obs])
        observations.append(obs)
        seen.add(turn_id)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp = output_path.with_suffix(output_path.suffix + ".tmp")
        temp.write_text(json.dumps(observations, indent=2), encoding="utf-8")
        temp.replace(output_path)
    return handoff(observations)


def fixture_observer(turn_id, prefix):
    """Deterministic local fixture for wiring tests; not an emotional inference."""
    return {"turn_id": turn_id, "states": {}, "triggers": [],
            "direction": "unknown", "evidence": [],
            "observer": "fixture-no-inference", "source": "assistant_reply"}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("transcript")
    p.add_argument("observations")
    p.add_argument("--live", action="store_true", help="Use DefAPI Jev observer")
    args = p.parse_args()
    turns = json.loads(Path(args.transcript).read_text(encoding="utf-8"))
    if args.live:
        from jev_defapi import observe
        def live_observer(turn_id, prefix):
            reply = prefix[-1]["content"]
            result = observe(reply, turn_id=turn_id)
            result["evidence"] = [reply[:240]] if reply.strip() else []
            return result
        observer = live_observer
    else:
        observer = fixture_observer
    print(json.dumps(iterate(turns, observer, args.observations), indent=2))
