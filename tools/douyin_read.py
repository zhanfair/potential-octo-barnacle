#!/usr/bin/env python3
"""Parse a Douyin share link into basic metadata and a playable/download URL."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

import requests


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/121.0.2277.107 "
        "Version/17.0 Mobile/15E148 Safari/604.1"
    )
}


def extract_first_url(text: str) -> str:
    match = re.search(r"https?://[^\s]+", text)
    if not match:
        raise ValueError("No URL found in input.")
    return match.group(0).rstrip("，。,.")


def resolve_video_id(share_text: str) -> str:
    share_url = extract_first_url(share_text)
    response = requests.get(share_url, headers=HEADERS, timeout=20, allow_redirects=True)
    response.raise_for_status()
    path_parts = [part for part in urlparse(response.url).path.split("/") if part]
    if not path_parts:
        raise ValueError(f"Could not resolve video id from {response.url}")
    return path_parts[-1]


def parse_router_data(html: str) -> dict:
    pattern = re.compile(r"window\._ROUTER_DATA\s*=\s*(.*?)</script>", re.DOTALL)
    match = pattern.search(html)
    if not match:
        raise ValueError("Could not find ROUTER_DATA in Douyin page.")
    return json.loads(unescape(match.group(1).strip()))


def pick_item(router_data: dict) -> dict:
    loader_data = router_data.get("loaderData", {})
    for key in ("video_(id)/page", "note_(id)/page"):
        if key in loader_data:
            return loader_data[key]["videoInfoRes"]["item_list"][0]
    raise ValueError("Could not find video or note item in ROUTER_DATA.")


def parse_douyin(share_text: str) -> dict:
    video_id = resolve_video_id(share_text)
    page_url = f"https://www.iesdouyin.com/share/video/{video_id}"
    response = requests.get(page_url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    item = pick_item(parse_router_data(response.text))
    video = item.get("video", {})
    play_addr = video.get("play_addr", {})
    url_list = play_addr.get("url_list") or []
    download_url = url_list[0].replace("playwm", "play") if url_list else ""

    author = item.get("author", {}) or {}
    stats = item.get("statistics", {}) or {}
    return {
        "status": "success",
        "video_id": video_id,
        "title": (item.get("desc") or "").strip(),
        "author": {
            "nickname": author.get("nickname"),
            "unique_id": author.get("unique_id"),
            "sec_uid": author.get("sec_uid"),
        },
        "stats": {
            "digg_count": stats.get("digg_count"),
            "comment_count": stats.get("comment_count"),
            "share_count": stats.get("share_count"),
            "collect_count": stats.get("collect_count"),
        },
        "download_url": download_url,
        "page_url": page_url,
    }


def safe_filename(value: str, fallback: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return (cleaned or fallback)[:120]


def download_video(download_url: str, output_path: Path) -> None:
    response = requests.get(download_url, headers=HEADERS, timeout=60, stream=True)
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                handle.write(chunk)


def extract_frames(video_path: Path, frames_dir: Path, count: int = 8) -> list[str]:
    import cv2

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
    if total_frames <= 0:
        raise ValueError("Could not read frame count from video.")

    frames_dir.mkdir(parents=True, exist_ok=True)
    sample_count = max(1, min(count, total_frames))
    positions = [
        int((index + 1) * total_frames / (sample_count + 1))
        for index in range(sample_count)
    ]

    saved: list[str] = []
    for index, frame_no in enumerate(positions, start=1):
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ok, frame = capture.read()
        if not ok:
            continue
        timestamp = frame_no / fps if fps else 0
        output_path = frames_dir / f"frame_{index:02d}_{timestamp:06.2f}s.jpg"
        cv2.imwrite(str(output_path), frame)
        saved.append(str(output_path.resolve()))

    capture.release()
    return saved


def transcribe_with_dashscope(media_url: str, context: str | None = None) -> dict:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return {
            "status": "skipped",
            "reason": "DASHSCOPE_API_KEY is not set.",
        }

    from douyin_mcp_server.asr_module import create_asr_instance

    asr = create_asr_instance(api_key, "qwen3-asr-flash")
    result = asr.recognize_url(
        audio_url=media_url,
        context=context,
        language="zh",
        enable_lid=True,
        enable_itn=False,
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse a Douyin share link.")
    parser.add_argument("share_text", help="Douyin share URL or full share text.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    parser.add_argument(
        "--download-to",
        help="Directory or .mp4 path for saving the video.",
    )
    parser.add_argument(
        "--frames-to",
        help="Directory for saving sampled video frames. Implies video download.",
    )
    parser.add_argument(
        "--frame-count",
        type=int,
        default=8,
        help="Number of sampled frames to save with --frames-to.",
    )
    parser.add_argument(
        "--transcribe",
        action="store_true",
        help="Transcribe speech with DashScope. Requires DASHSCOPE_API_KEY.",
    )
    parser.add_argument(
        "--context",
        help="Optional ASR context words, such as names or domain terms.",
    )
    args = parser.parse_args()

    try:
        result = parse_douyin(args.share_text)
        saved_video_path = None
        if (args.download_to or args.frames_to) and result.get("download_url"):
            requested_path = Path(args.download_to or args.frames_to or ".")
            if requested_path.suffix.lower() != ".mp4":
                name = safe_filename(result.get("title", ""), result["video_id"])
                requested_path = requested_path / f"{result['video_id']}_{name}.mp4"
            download_video(result["download_url"], requested_path)
            saved_video_path = requested_path.resolve()
            result["saved_video"] = str(saved_video_path)

        if args.frames_to and saved_video_path:
            frames_dir = Path(args.frames_to) / f"{result['video_id']}_frames"
            result["saved_frames"] = extract_frames(
                saved_video_path,
                frames_dir,
                count=args.frame_count,
            )

        if args.transcribe and result.get("download_url"):
            result["transcript"] = transcribe_with_dashscope(
                result["download_url"],
                context=args.context,
            )
    except Exception as exc:
        result = {"status": "error", "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
