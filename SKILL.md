---
name: mywant-smartgolf-check-reserved-plugin
description: スマートゴルフ（北新宿・中野新橋・新中野）の予約一覧ページにアクセスし、現在時刻より将来の予約が存在するかどうかを確認する。予約済み判定・予約内容の確認が必要なときに使用する。Playwright経由でChromeのCDPに接続する。
compatibility:
  python: ">=3.10"
  requires:
    - playwright (sync_api)
    - Chrome with remote debugging on port 9222
    - smartgolf.stores.jp にログイン済みのChrome
metadata:
  output-format: json
  json-schema: see "出力JSON形式" section below
---

## 使い方

```bash
python3 "${CLAUDE_SKILL_DIR}/main.py"
```

引数なし。ChromeのリモートデバッグとChromeがsmartgolf.stores.jpにログイン済みであることが前提条件。

## 出力JSON形式

```json
{
  "is_reserved": true,
  "reservations": [
    {
      "datetime": "2026/04/12 20:00",
      "store": "中野新橋店",
      "room": "打席予約(Room02)",
      "status": "confirmed"
    }
  ],
  "checked_at": "2026-04-12 15:30"
}
```

予約がない場合:

```json
{
  "is_reserved": false,
  "reservations": [],
  "checked_at": "2026-04-12 15:30"
}
```

### フィールド説明

| フィールド | 型 | 説明 |
|---|---|---|
| `is_reserved` | boolean | 現在時刻より将来の予約が1件以上存在する場合 `true` |
| `reservations` | array | 取得した予約リスト（過去予約含む全件） |
| `reservations[n].datetime` | string | 予約日時テキスト（ページ表示のまま） |
| `reservations[n].store` | string | 店舗名（取得できた場合） |
| `reservations[n].room` | string | 部屋名（取得できた場合） |
| `reservations[n].status` | string | 予約ステータス（ページ表示のまま） |
| `checked_at` | string | 確認実行時刻（JST, YYYY-MM-DD HH:MM形式） |

### エラー時

```json
{ "error": "エラーの説明文", "is_reserved": false, "reservations": [] }
```
