---
name: reddit-summary
description: ポケモンスリープ Reddit 人気投稿の要約
---

r/PokemonSleep の今日の人気投稿を取得して日本語で要約します。

---

## トップ投稿モード

### 1. データの取得

以下のコマンドを実行してください。

```
venv/Scripts/python reddit_summary.py
```

コマンドに失敗したときは、エラー内容をユーザーに伝えてください。

### 2. 投稿の要約

スクリプトの出力をもとに、各投稿を以下の形式で日本語で要約してください。

- タイトルは英語から自然な日本語に翻訳する
- 本文がある場合は内容を1〜2文で要約する

#### 出力例

以下の内容を複数行メッセージとして送信してください。

```
📋 r/PokemonSleep トップ投稿 (2026-02-21)

🥇 カビゴンが眠気パワー100%に到達！
   → 達成記念のスクリーンショットを投稿。
   https://www.reddit.com/r/PokemonSleep/comments/xxxxxx/...

🥈 今週のリサーチ結果 - マンムー島
   → 今週の睡眠リサーチ報告。平均スコアは〇〇点だった。
   https://www.reddit.com/r/PokemonSleep/comments/yyyyyy/...

...（上位10件）
```
