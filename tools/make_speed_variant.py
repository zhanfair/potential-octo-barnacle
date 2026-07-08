from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import imageio_ffmpeg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a speed-adjusted copy of WAV segments.")
    parser.add_argument("--input-dir", default="voice_outputs/miyazaki_first_video/raw")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--speed", type=float, required=True)
    return parser.parse_args()


def speed_label(speed: float) -> str:
    return f"speed{round(speed * 100):03d}"


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir)
    label = speed_label(args.speed)
    output_dir = Path(args.output_dir or input_dir.parent / label)
    output_dir.mkdir(parents=True, exist_ok=True)

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    wav_files = sorted(input_dir.glob("*.wav"))
    if not wav_files:
        raise FileNotFoundError(f"No wav files found in {input_dir}")

    for index, input_path in enumerate(wav_files, start=1):
        output_path = output_dir / f"{input_path.stem}_{label}.wav"
        print(f"[{index}/{len(wav_files)}] {input_path.name} -> {output_path.name}")
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(input_path),
                "-filter:a",
                f"atempo={args.speed}",
                str(output_path),
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
