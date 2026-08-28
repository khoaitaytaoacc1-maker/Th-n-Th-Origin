import os, re, json, html
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

PAGE_URL = os.getenv("FACEBOOK_PAGE_URL", "https://www.facebook.com/thanthuorigin")
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
STATE_FILE = Path("state.json")
MAX_POSTS = 10

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"seen": []}

def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def canonicalize(url):
    url = html.unescape(url)
    url = url.replace("\\/", "/")
    if url.startswith("/"):
        url = urljoin("https://www.facebook.com", url)
    # Strip tracking parameters; keep the post identifier/path.
    p = urlparse(url)
    if p.netloc and "facebook.com" in p.netloc:
        return f"https://www.facebook.com{p.path}" + (f"?{p.query}" if "story_fbid" in p.query else "")
    return url

def extract_posts(text):
    soup = BeautifulSoup(text, "html.parser")
    found = []

    # Normal anchors.
    for a in soup.find_all("a", href=True):
        href = canonicalize(a["href"])
        if is_post_url(href):
            title = a.get_text(" ", strip=True)
            found.append((href, title))

    # Facebook frequently embeds links inside JSON/script data.
    patterns = [
        r'https?://(?:www|m)\.facebook\.com/[^"\']*/posts/[^"\']+',
        r'https?://(?:www|m)\.facebook\.com/permalink\.php\?[^"\']*story_fbid[^"\']+',
        r'"/[^"]*/posts/[^"]+"',
    ]
    for pattern in patterns:
        for match in re.findall(pattern, text):
            found.append((canonicalize(match), ""))

    # De-duplicate while preserving order.
    out, seen = [], set()
    for url, title in found:
        if url not in seen and is_post_url(url):
            seen.add(url)
            out.append((url, title))
    return out[:MAX_POSTS]

def is_post_url(url):
    u = url.lower()
    return (
        "facebook.com" in u and
        ("/posts/" in u or "/permalink.php" in u or "story_fbid=" in u)
    )

def fetch_page(url):
    r = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
    r.raise_for_status()
    return r.text

def send_discord(post_url, title=""):
    content = "📢 **Thần Thú Origin vừa đăng bài mới!**\n" + post_url
    if title:
        title = re.sub(r"\s+", " ", title).strip()
        if len(title) > 300:
            title = title[:297] + "..."
        content = f"📢 **Thần Thú Origin vừa đăng bài mới!**\n{title}\n{post_url}"

    r = requests.post(
        WEBHOOK_URL,
        json={"content": content, "allowed_mentions": {"parse": []}},
        timeout=20,
    )
    r.raise_for_status()

def main():
    state = load_state()
    seen = set(state.get("seen", []))

    try:
        page = fetch_page(PAGE_URL)
        posts = extract_posts(page)
    except Exception as e:
        print(f"Facebook fetch failed: {e}")
        return

    if not posts:
        print("No public post links were found. Facebook may be blocking/limiting automated access.")
        return

    # The page usually returns newest first. Only send posts we have not seen.
    new_posts = [(u, t) for u, t in reversed(posts) if u not in seen]

    # First run: do not spam old posts; mark the current batch as seen.
    if not seen:
        for u, _ in posts:
            seen.add(u)
        save_state({"seen": list(seen)[-100:]})
        print(f"First run: initialized with {len(posts)} existing post(s). No Discord notifications sent.")
        return

    for url, title in new_posts:
        try:
            send_discord(url, title)
            print("Sent:", url)
            seen.add(url)
        except Exception as e:
            print(f"Discord send failed for {url}: {e}")

    save_state({"seen": list(seen)[-100:]})

if __name__ == "__main__":
    main()
