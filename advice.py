#!/usr/bin/env python3
"""SmartGolf's advice on its answer (engine/core/want_advice.go): a
reservation that came (change: added) means a round of practice — take the
glove and the shoes. Told with the murmur to the wants that hear it (a
checklist of things to take proposes them)."""
import json
import sys


def main() -> None:
    given = json.loads(sys.argv[1])
    advice = []
    for change in given.get("change") or []:
        if change.get("kind") != "added":
            continue
        for item in change.get("items") or []:
            r = item.get("value") or {}
            store = r.get("store") or (item.get("labels") or {}).get("place") or ""
            when = (r.get("datetime") or "")[5:].replace("-", "/")
            why = f"{store} {when}の練習".strip()
            advice += [{"kind": "bring", "item": "ゴルフグローブ", "why": why},
                       {"kind": "bring", "item": "ゴルフシューズ", "why": why}]
            break
    print(json.dumps({"advice": advice}, ensure_ascii=False))


if __name__ == "__main__":
    main()
