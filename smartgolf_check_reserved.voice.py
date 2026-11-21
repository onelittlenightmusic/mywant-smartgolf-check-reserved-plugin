"""SmartGolf の声。台詞は持たず（"say" を返さない：既定の台詞のまま）、
つぶやきに決まった形のラベルを付けるためにある — 予約ができたとき（booked）、
その予約の時刻（time, RFC3339）と場所（place：店舗）。それを聞いた want
（spec.hear：近くの天気など）は、文面を読み解かずにラベルで分かる。

選ぶ予約は、今回新しく見つかったもの（main.py が "new": true を付ける）、
無ければ次の予約（答え）。
"""
import json
import sys


def place_of(r: dict) -> str:
    store = (r.get("store") or "").strip()
    if not store:
        room = r.get("room") or ""
        store = room.split("/")[0].strip() if "/" in room else ""
    return store


def pick(want: dict):
    state = want.get("state") or {}
    for r in state.get("reservations") or []:
        if isinstance(r, dict) and r.get("new"):
            return r
    r = (want.get("event") or {}).get("result")
    return r if isinstance(r, dict) else None


def main() -> None:
    want = json.loads(sys.argv[1])
    out = {}
    r = pick(want) if (want.get("event") or {}).get("kind") == "output" else None
    if r:
        labels = {}
        if r.get("datetime_rfc3339"):
            labels["time"] = r["datetime_rfc3339"]
        if place_of(r):
            labels["place"] = place_of(r)
        if labels:
            out["labels"] = labels
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
