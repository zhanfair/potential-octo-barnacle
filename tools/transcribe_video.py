#!/usr/bin/env python3
"""Transcribe a local video/audio file with faster-whisper."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from faster_whisper import WhisperModel


def format_timestamp(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(segments: list[dict], path: Path) -> None:
    lines: list[str] = []
    for index, segment in enumerate(segments, start=1):
        lines.append(str(index))
        lines.append(
            f"{format_timestamp(segment['start'])} --> "
            f"{format_timestamp(segment['end'])}"
        )
        lines.append(segment["text"].strip())
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_txt(segments: list[dict], path: Path, with_timestamps: bool) -> None:
    lines: list[str] = []
    for segment in segments:
        text = segment["text"].strip()
        if not text:
            continue
        if with_timestamps:
            lines.append(
                f"[{segment['start']:.2f}-{segment['end']:.2f}] {text}"
            )
        else:
            lines.append(text)
    path.write_text("\n".join(lines), encoding="utf-8")


def transcribe(
    media_path: Path,
    output_dir: Path,
    model_name: str,
    language: str,
    compute_type: str,
    with_timestamps: bool,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    model = WhisperModel(
        model_name,
        device="cpu",
        compute_type=compute_type,
    )
    segments_iter, info = model.transcribe(
        str(media_path),
        language=language,
        vad_filter=True,
        beam_size=5,
    )
    segments = [
        {
            "start": segment.start,
            "end": segment.end,
            "text": segment.text,
        }
        for segment in segments_iter
    ]

    stem = media_path.stem
    txt_path = output_dir / f"{stem}.{model_name}.txt"
    srt_path = output_dir / f"{stem}.{model_name}.srt"
    json_path = output_dir / f"{stem}.{model_name}.json"

    write_txt(segments, txt_path, with_timestamps=with_timestamps)
    write_srt(segments, srt_path)
    json_path.write_text(
        json.dumps(
            {
                "media": str(media_path.resolve()),
                "model": model_name,
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "segments": segments,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "status": "success",
        "media": str(media_path.resolve()),
        "model": model_name,
        "language": info.language,
        "duration": info.duration,
        "text": str(txt_path.resolve()),
        "srt": str(srt_path.resolve()),
        "json": str(json_path.resolve()),
        "segments": len(segments),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcribe video/audio locally.")
    parser.add_argument("media", help="Path to a local video/audio file.")
    parser.add_argument("--output-dir", default="transcripts")
    parser.add_argument("--model", default="small", help="tiny/base/small/medium/large-v3")
    parser.add_argument("--language", default="zh", help="Language code, e.g. zh")
    parser.add_argument("--compute-type", default="int8", help="int8 is best for CPU")
    parser.add_argument("--timestamps", action="store_true")
    args = parser.parse_args()

    result = transcribe(
        media_path=Path(args.media),
        output_dir=Path(args.output_dir),
        model_name=args.model,
        language=args.language,
        compute_type=args.compute_type,
        with_timestamps=args.timestamps,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
