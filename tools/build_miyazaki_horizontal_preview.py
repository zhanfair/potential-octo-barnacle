from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import imageio_ffmpeg
import soundfile as sf


CLIP_MAP = {
    "S01": "S01_EP01_0027_0141_studio_arrival.mkv",
    "S02": "BROLL_EP01_0244_0259_starts_drawing.mkv",
    "S03": "S04_EP01_0845_0959_no_script_image_board.mkv",
    "S04": "S04_EP01_1307_1342_first_image_flows.mkv",
    "S05": "BROLL_EP01_4212_4325_pencil_storyboard.mkv",
    "S06": "S06_EP01_2352_2757_pastel_simple_lines.mkv",
    "S07": "S07_EP02_0440_0642_redraw_ponyo_emotion.mkv",
    "S08": "BROLL_EP01_3755_3935_sea_life_empty_shots.mkv",
    "S09": "S09_EP02_4202_4659_toki_hug_memory.mkv",
    "S10": "S06_EP02_0203_0216_no_cg_hand_drawn.mkv",
    "S11": "S11_EP04_2007_2138_age_toll.mkv",
    "S12": "BROLL_EP01_4212_4325_pencil_storyboard.mkv",
    "S13": "S13_EP04_4006_4137_naoko_folds_shirt.mkv",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a horizontal no-subtitle Miyazaki preview video.")
    parser.add_argument("--audio-dir", default="voice_outputs/miyazaki_first_video/speed110")
    parser.add_argument("--full-audio", default="voice_outputs/miyazaki_first_video/miyazaki_first_video_full_speed110.wav")
    parser.add_argument("--clip-dir", default="video_clips/miyazaki_first_video")
    parser.add_argument("--output-dir", default="video_outputs/miyazaki_first_video_horizontal_preview")
    parser.add_argument("--gap", type=float, default=0.35)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    return parser.parse_args()


def audio_duration(path: Path) -> float:
    info = sf.info(path)
    return info.frames / info.samplerate


def find_audio(audio_dir: Path, section_id: str) -> Path:
    matches = sorted(audio_dir.glob(f"{section_id}_*_speed110.wav"))
    if not matches:
        raise FileNotFoundError(f"No audio segment found for {section_id}")
    return matches[0]


def run(command: list[str]) -> None:
    print(" ".join(command))
    subprocess.run(command, check=True)


def main() -> None:
    args = parse_args()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    output_dir = Path(args.output_dir)
    segment_dir = output_dir / "segments"
    output_dir.mkdir(parents=True, exist_ok=True)
    segment_dir.mkdir(parents=True, exist_ok=True)

    section_ids = [f"S{i:02d}" for i in range(1, 14)]
    segment_paths: list[Path] = []
    for index, section_id in enumerate(section_ids):
        audio_path = find_audio(Path(args.audio_dir), section_id)
        duration = audio_duration(audio_path)
        if index < len(section_ids) - 1:
            duration += args.gap

        clip_path = Path(args.clip_dir) / CLIP_MAP[section_id]
        if not clip_path.exists():
            fallback = Path(args.clip_dir) / "S01_EP01_0027_0141_studio_arrival.mkv"
            print(f"Missing {clip_path}, fallback to {fallback}")
            clip_path = fallback

        segment_path = segment_dir / f"{section_id}.mp4"
        vf = (
            f"scale={args.width}:{args.height}:force_original_aspect_ratio=increase,"
            f"crop={args.width}:{args.height},"
            "eq=brightness=-0.03:contrast=0.98:saturation=0.96,"
            "format=yuv420p"
        )
        run(
            [
                ffmpeg,
                "-y",
                "-stream_loop",
                "-1",
                "-i",
                str(clip_path),
                "-t",
                f"{duration:.3f}",
                "-vf",
                vf,
                "-an",
                "-r",
                "30",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-crf",
                "26",
                str(segment_path),
            ]
        )
        segment_paths.append(segment_path)

    concat_path = output_dir / "concat.txt"
    concat_path.write_text(
        "\n".join(f"file '{path.resolve().as_posix()}'" for path in segment_paths),
        encoding="utf-8",
    )
    base_path = output_dir / "miyazaki_horizontal_base.mp4"
    run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), "-c", "copy", str(base_path)])

    final_path = output_dir / "miyazaki_first_video_horizontal_no_subs_speed110.mp4"
    run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(base_path),
            "-i",
            args.full_audio,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "22",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-shortest",
            str(final_path),
        ]
    )
    print(f"Wrote {final_path}")


if __name__ == "__main__":
    main()
