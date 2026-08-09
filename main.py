import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

# mrs_browser ships as the "machine-readable-skills-browser" custom; a checkout
# at ~/work wins when present so a development copy still overrides it.
for _mrs_path in ("~/work/machine-readable-skills-browser",
                  "~/.mywant/custom-types/machine-readable-skills-browser"):
    _mrs_path = os.path.expanduser(_mrs_path)
    if os.path.isdir(_mrs_path):
        sys.path.insert(0, _mrs_path)
        break
from mrs_browser import browser_run  # noqa: E402

JST = timezone(timedelta(hours=9))
RESERVATIONS_URL = "https://smartgolf.stores.jp/reserve/u"

# "Sun, April 12, 2026 19:00（60 minutes）" → parse up to "19:00"
_DT_PATTERN = re.compile(
    r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+'
    r'(\w+)\s+(\d{1,2}),\s+(\d{4})\s+(\d{2}:\d{2})'
)
_MONTH_MAP = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}


def parse_datetime_line(line):
    """ページの日付行をdatetimeに変換する。失敗時はNoneを返す"""
    m = _DT_PATTERN.search(line)
    if not m:
        return None
    month_name, day, year, hm = m.group(1), m.group(2), m.group(3), m.group(4)
    month = _MONTH_MAP.get(month_name)
    if not month:
        return None
    try:
        hour, minute = map(int, hm.split(":"))
        return datetime(int(year), month, int(day), hour, minute, tzinfo=JST)
    except ValueError:
        return None


def report_progress(percentage, message=""):
    print(json.dumps({"_progress": percentage, "_message": message}, ensure_ascii=False), flush=True)


def main():
    try:
        report_progress(5, "Opening reservations page")
        result = browser_run(RESERVATIONS_URL, [
            {"type": "customStep", "name": "read",
             "parameters": {"selector": "body", "extract": "text", "as": "body_text", "timeout_ms": 8000}},
        ])

        report_progress(50, "Parsing reservation data")
        now_jst = datetime.now(JST)

        body_text = result.get("body_text") or ""
        lines = [l.strip() for l in body_text.split("\n") if l.strip()]

        # ページ構造:
        #   Approved
        #   <店名> 打席予約ページ
        #   <店名>/<部屋名>
        #   <曜日>, <月> <日>, <年> <HH:MM>（60 minutes）
        #   No Preference
        #   SMART GOLF <店名>
        reservations = []
        i = 0
        while i < len(lines):
            if lines[i] in ("Approved", "Cancelled", "Pending"):
                status = lines[i]
                room = lines[i + 2] if i + 2 < len(lines) else ""
                dt_line = lines[i + 3] if i + 3 < len(lines) else ""
                dt_obj = parse_datetime_line(dt_line)
                if dt_obj:
                    store = room.split("/")[0] if "/" in room else ""
                    reservations.append({
                        "datetime": dt_obj.strftime("%Y-%m-%d %H:%M"),
                        # 同じ時刻をRFC3339でも出す。表示用の "datetime" は人が
                        # 読むためのもので、reminder want の event_time は
                        # time.Parse(time.RFC3339) しか受け付けないため。
                        "datetime_rfc3339": dt_obj.isoformat(),
                        "store": store,
                        "room": room,
                        "status": status,
                        "is_future": dt_obj > now_jst,
                    })
                i += 1
            else:
                i += 1

        future_reservations = [r for r in reservations if r.get("is_future")]
        is_reserved = len(future_reservations) > 0

        for r in reservations:
            r.pop("is_future", None)

        output = {
            "is_reserved": is_reserved,
            "reservations": future_reservations,  # 過去の予約は除外
            "checked_at": now_jst.strftime("%Y-%m-%d %H:%M"),
        }
        report_progress(100, "Done")
        print(json.dumps(output, ensure_ascii=False), flush=True)

    except SystemExit:
        raise
    except Exception as e:
        print(json.dumps({"error": str(e), "is_reserved": False, "reservations": []}, ensure_ascii=False), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
