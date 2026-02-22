import sys
import io
import json
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

# Windows cp932 対策
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

POSTS_URL = "https://www.reddit.com/r/PokemonSleep/top.json?t=day&limit=10"
COMMENTS_URL = "https://www.reddit.com/r/PokemonSleep/comments/{post_id}.json?sort=best&limit={limit}"
HEADERS = {"User-Agent": "pksl-record/1.0"}


def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error: HTTP {e.code} ({url})", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def fetch_top_comments(post_id, limit):
    data = fetch_json(COMMENTS_URL.format(post_id=post_id, limit=limit))
    comments = []
    for child in data[1]["data"]["children"]:
        c = child.get("data", {})
        body = c.get("body", "").strip()
        score = c.get("score", 0)
        if body and body != "[deleted]" and body != "[removed]":
            comments.append({"body": body, "score": score})
    return comments[:limit]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--comments", type=int, default=0, metavar="N",
                        help="各投稿の人気コメントを N 件取得する (デフォルト: 0=取得しない)")
    args = parser.parse_args()

    data = fetch_json(POSTS_URL)
    posts = data["data"]["children"]

    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    print(f"取得日時: {now}")
    print("期間: 過去24時間のトップ投稿 (r/PokemonSleep)")
    print()

    for i, post in enumerate(posts, 1):
        p = post["data"]
        title = p.get("title", "")
        score = p.get("score", 0)
        num_comments = p.get("num_comments", 0)
        url = "https://www.reddit.com" + p.get("permalink", "")
        selftext = p.get("selftext", "").strip()
        body = selftext[:300] + ("..." if len(selftext) > 300 else "") if selftext else "(画像/リンク投稿)"
        print(f"[{i}] {title}")
        print(f"    スコア: {score:,} | コメント: {num_comments}")
        print(f"    URL: {url}")
        print(f"    本文: {body}")

        if args.comments > 0:
            post_id = p.get("id", "")
            comments = fetch_top_comments(post_id, args.comments)
            if comments:
                print(f"    人気コメント ({len(comments)}件):")
                for c in comments:
                    text = c["body"][:200] + ("..." if len(c["body"]) > 200 else "")
                    print(f"      [{c['score']:,}点] {text}")

        print()


if __name__ == "__main__":
    main()
