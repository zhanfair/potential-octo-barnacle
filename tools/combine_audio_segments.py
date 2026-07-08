from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Combine generated narration segments into one WAV.")
    parser.add_argument("--manifest", default="voice_outputs/miyazaki_first_video/manifest.json")
    parser.add_argument("--variant", choices=["raw", "speed"], default="speed")
    parser.add_argument("--speed-label", default="speed115")
    parser.add_argument("--gap", type=float, default=0.35)
    parser.add_argument("--output", default=None)
    return parser.parse_args()


def resolve_audio_path(raw_path: str, speed_label: str) -> Path:
    fixed = Path(raw_path.replace("speed114", speed_label).replace("speed115", speed_label))
    if fixed.exists():
        return fixed

    path = Path(raw_path)
    if path.exists():
        return path

    raise FileNotFoundError(raw_path)


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    key = "raw_path" if args.variant == "raw" else "speed_path"

    suffix = args.variant if args.variant == "raw" else args.speed_label
    output_path = Path(args.output or manifest_path.parent / f"miyazaki_first_video_full_{suffix}.wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    segment_paths = [resolve_audio_path(item[key], args.speed_label) for item in manifest["sections"]]
    first_info = sf.info(segment_paths[0])
    gap_frames = int(first_info.samplerate * args.gap)
    silence = np.zeros((gap_frames, first_info.channels), dtype="float32")

    total_frames = 0
    with sf.SoundFile(
        output_path,
        mode="w",
        samplerate=first_info.samplerate,
        channels=first_info.channels,
        subtype=first_info.subtype,
    ) as out_file:
        for index, path in enumerate(segment_paths):
            with sf.SoundFile(path) as in_file:
                while True:
                    chunk = in_file.read(48000, dtype="float32", always_2d=True)
                    if len(chunk) == 0:
                        break
                    out_file.write(chunk)
                    total_frames += len(chunk)
            if index < len(segment_paths) - 1 and gap_frames:
                out_file.write(silence)
                total_frames += gap_frames

    duration = round(total_frames / first_info.samplerate, 3)
    print(f"Wrote {output_path}")
    print(f"Duration: {duration}s")


if __name__ == "__main__":
    main()
