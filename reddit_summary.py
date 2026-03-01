import sys
import io
import json
import re
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

# Windows cp932 対策
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith('cp'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

POSTS_URL = "https://www.reddit.com/r/PokemonSleep/top.json?t=day&limit=10"
COMMENTS_URL = "https://www.reddit.com/r/PokemonSleep/comments/{post_id}.json?sort=best&limit={limit}"
POST_URL = "https://www.reddit.com/comments/{post_id}.json?sort=best&limit={limit}"
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


def extract_post_id(url):
    m = re.search(r'/comments/([a-z0-9]+)', url)
    if not m:
        print(f"Error: URL から post_id を抽出できませんでした: {url}", file=sys.stderr)
        sys.exit(1)
    return m.group(1)


def fetch_post_by_url(url, num_comments):
    post_id = extract_post_id(url)
    limit = max(num_comments, 1)
    data = fetch_json(POST_URL.format(post_id=post_id, limit=limit))

    p = data[0]["data"]["children"][0]["data"]
    title = p.get("title", "")
    score = p.get("score", 0)
    num_cmts = p.get("num_comments", 0)
    permalink = "https://www.reddit.com" + p.get("permalink", "")
    selftext = p.get("selftext", "").strip()

    comments = []
    for child in data[1]["data"]["children"]:
        c = child.get("data", {})
        body = c.get("body", "").strip()
        cscore = c.get("score", 0)
        if body and body != "[deleted]" and body != "[removed]":
            comments.append({"body": body, "score": cscore})
    comments = comments[:num_comments]

    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    print(f"取得日時: {now}")
    print(f"URL: {permalink}")
    print()
    print(f"タイトル: {title}")
    print(f"スコア: {score:,} | コメント: {num_cmts}")
    print()
    if selftext:
        print(f"本文:\n{selftext}")
    else:
        print("本文: (画像/リンク投稿)")
    print()

    if comments:
        print(f"人気コメント ({len(comments)}件):")
        for c in comments:
            print(f"  [{c['score']:,}点] {c['body']}")
            print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--comments", type=int, default=0, metavar="N",
                        help="各投稿の人気コメントを N 件取得する (デフォルト: 0=取得しない)")
    parser.add_argument("--url", type=str, default=None, metavar="URL",
                        help="特定の Reddit 投稿 URL を指定して詳細取得する")
    args = parser.parse_args()

    if args.url:
        num_comments = args.comments if args.comments > 0 else 50
        fetch_post_by_url(args.url, num_comments)
        return

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
