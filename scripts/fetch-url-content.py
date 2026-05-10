#!/usr/bin/env python3
"""URL/YouTube 본문 추출기.

Usage:
    python3 fetch-url-content.py <url> [<url> ...]

stdout에 각 URL별로 다음 형식의 블록을 출력한다:

    === FETCHED FROM <url> ===
    <본문 (truncated if necessary)>

실패한 URL은 동일 형식으로 짧은 에러 메시지를 적는다 — 호출 측에서 파이프라인을
중단할 필요가 없도록.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request

MAX_LEN_PER_URL = 8000
HTTP_TIMEOUT = 15
YT_DLP_TIMEOUT = 30
YOUTUBE_RE = re.compile(r"(?:^|\.)(youtube\.com|youtu\.be)$|(?:youtube\.com|youtu\.be)(?:/|$)")
USER_AGENT = "Mozilla/5.0 (compatible; bbl-idea-elaborator/1.0)"


def is_youtube(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url


def fetch_youtube(url: str) -> str:
    try:
        proc = subprocess.run(
            ["yt-dlp", "--skip-download", "--dump-json", "--no-warnings", url],
            capture_output=True,
            text=True,
            timeout=YT_DLP_TIMEOUT,
            check=True,
        )
    except FileNotFoundError:
        return "[yt-dlp not installed]"
    except subprocess.TimeoutExpired:
        return "[yt-dlp timeout]"
    except subprocess.CalledProcessError as e:
        return f"[yt-dlp failed: {e.stderr.strip()[:200] or e.returncode}]"

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return f"[yt-dlp json parse failed: {e}]"

    title = data.get("title", "")
    channel = data.get("channel") or data.get("uploader") or ""
    duration = data.get("duration_string") or ""
    desc = (data.get("description") or "").strip()
    video_id = data.get("id")

    parts = [f"Title: {title}"]
    if channel:
        parts.append(f"Channel: {channel}")
    if duration:
        parts.append(f"Duration: {duration}")
    if desc:
        parts.append(f"\nDescription:\n{desc}")

    transcript = _fetch_youtube_transcript(video_id) if video_id else ""
    if transcript:
        parts.append(f"\nTranscript:\n{transcript}")

    return "\n".join(parts)


def _fetch_youtube_transcript(video_id: str) -> str:
    """youtube-transcript-api >= 1.0 (instance API). Returns empty on any failure."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
    except ImportError:
        return ""
    api = YouTubeTranscriptApi()
    try:
        fetched = api.fetch(video_id, languages=("ko", "en"))
    except Exception:
        try:
            listing = api.list(video_id)
            tr = next(iter(listing), None)
            if tr is None:
                return ""
            fetched = tr.fetch()
        except Exception as e:
            return f"[transcript unavailable: {type(e).__name__}]"
    try:
        snippets = list(fetched)
    except Exception:
        return ""
    return " ".join(getattr(s, "text", "") for s in snippets if getattr(s, "text", ""))


def fetch_html(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            raw = resp.read()
        html = raw.decode(charset, errors="replace")
    except urllib.error.HTTPError as e:
        return f"[http {e.code}: {e.reason}]"
    except urllib.error.URLError as e:
        return f"[url error: {e.reason}]"
    except (TimeoutError, Exception) as e:
        return f"[fetch failed: {type(e).__name__}: {e}]"

    try:
        import trafilatura  # type: ignore

        extracted = trafilatura.extract(html, include_comments=False, include_tables=False)
        if extracted:
            return extracted.strip()
    except ImportError:
        pass

    stripped = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    stripped = re.sub(r"<style[^>]*>.*?</style>", " ", stripped, flags=re.DOTALL | re.IGNORECASE)
    stripped = re.sub(r"<[^>]+>", " ", stripped)
    stripped = re.sub(r"\s+", " ", stripped).strip()
    return stripped or "[no extractable content]"


def truncate(text: str, limit: int = MAX_LEN_PER_URL) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n[... truncated {len(text) - limit} chars]"


def main(argv: list[str]) -> int:
    if not argv:
        return 0
    blocks: list[str] = []
    for url in argv:
        try:
            content = fetch_youtube(url) if is_youtube(url) else fetch_html(url)
        except Exception as e:
            content = f"[unexpected error: {type(e).__name__}: {e}]"
        blocks.append(f"=== FETCHED FROM {url} ===\n{truncate(content)}")
    sys.stdout.write("\n\n".join(blocks))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
