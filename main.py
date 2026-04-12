import json
import sys
import time
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright

JST = timezone(timedelta(hours=9))
RESERVATIONS_URL = "https://smartgolf.stores.jp/reserve/u"


def error_out(message):
    print(json.dumps({"error": message, "is_reserved": False, "reservations": []}, ensure_ascii=False))
    sys.exit(1)


def parse_reservation_datetime(text):
    """予約日時テキストをdatetimeに変換する。失敗時はNoneを返す"""
    # 想定フォーマット例: "2026/04/12 20:00" or "2026-04-12 20:00" or "4月12日 20:00"
    formats = [
        "%Y/%m/%d %H:%M",
        "%Y-%m-%d %H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text.strip(), fmt).replace(tzinfo=JST)
        except ValueError:
            continue
    return None


def main():
    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.new_page()

            page.goto(RESERVATIONS_URL, wait_until="domcontentloaded")
            time.sleep(3)

            now_jst = datetime.now(JST)

            # ページの全テキストを取得
            body_text = page.inner_text("body")
            lines = [l.strip() for l in body_text.split("\n") if l.strip()]

            # 予約カード要素を探索
            # smartgolf の予約一覧ページは各予約が個別要素として表示されていることが多い
            reservation_items = page.query_selector_all('[class*="ReservationItem"], [class*="reservation-item"], [class*="Reservation"]')

            reservations = []

            if reservation_items:
                for item in reservation_items:
                    item_text = item.inner_text()
                    item_lines = [l.strip() for l in item_text.split("\n") if l.strip()]

                    datetime_str = None
                    store_name = None
                    room_name = None
                    status_text = None

                    for line in item_lines:
                        dt = parse_reservation_datetime(line)
                        if dt and datetime_str is None:
                            datetime_str = line.strip()
                        if "店" in line and store_name is None:
                            store_name = line.strip()
                        if "Room" in line and room_name is None:
                            room_name = line.strip()
                        if any(kw in line for kw in ["予約済み", "confirmed", "Confirmed", "予約確定"]) and status_text is None:
                            status_text = line.strip()

                    if datetime_str:
                        dt_obj = parse_reservation_datetime(datetime_str)
                        is_future = dt_obj is not None and dt_obj > now_jst
                        reservations.append({
                            "datetime": datetime_str,
                            "store": store_name or "",
                            "room": room_name or "",
                            "status": status_text or "confirmed",
                            "is_future": is_future,
                        })
            else:
                # フォールバック: テキスト全体から日時っぽい行を探す
                for i, line in enumerate(lines):
                    dt = parse_reservation_datetime(line)
                    if dt is None:
                        continue

                    is_future = dt > now_jst
                    store_name = ""
                    room_name = ""

                    # 前後数行から店名・部屋名を補完
                    context_lines = lines[max(0, i - 3):i + 4]
                    for cl in context_lines:
                        if "店" in cl and not store_name:
                            store_name = cl
                        if "Room" in cl and not room_name:
                            room_name = cl

                    reservations.append({
                        "datetime": line,
                        "store": store_name,
                        "room": room_name,
                        "status": "confirmed",
                        "is_future": is_future,
                    })

            page.close()

            future_reservations = [r for r in reservations if r.get("is_future")]
            is_reserved = len(future_reservations) > 0

            # is_future フィールドは内部用なので出力から除外
            for r in reservations:
                r.pop("is_future", None)

            output = {
                "is_reserved": is_reserved,
                "reservations": reservations,
                "checked_at": now_jst.strftime("%Y-%m-%d %H:%M"),
            }
            print(json.dumps(output, ensure_ascii=False))

    except SystemExit:
        raise
    except Exception as e:
        error_out(str(e))


if __name__ == "__main__":
    main()
