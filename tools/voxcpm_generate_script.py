from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg
import soundfile as sf
from voxcpm import VoxCPM


SECTION_RE = re.compile(r"^###\s+(S\d{2})\s+(.+?)\s*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate cloned narration from S01-style script sections.")
    parser.add_argument("--script", default="26_宫崎骏第一条视频完整口播稿.md")
    parser.add_argument("--reference-wav", default="voice_refs/user_reference_90.wav")
    parser.add_argument("--output-dir", default="voice_outputs/miyazaki_first_video")
    parser.add_argument("--cache-dir", default="pretrained_models")
    parser.add_argument("--model", default="openbmb/VoxCPM2")
    parser.add_argument("--speed", type=float, default=1.15)
    parser.add_argument("--cfg-value", type=float, default=2.0)
    parser.add_argument("--timesteps", type=int, default=10)
    parser.add_argument("--device", default=None)
    parser.add_argument("--load-denoiser", action="store_true")
    return parser.parse_args()


def speed_label(speed: float) -> str:
    return f"speed{round(speed * 100):03d}"


def extract_sections(script_path: Path) -> list[dict[str, str]]:
    lines = script_path.read_text(encoding="utf-8").splitlines()
    in_body = False
    current: dict[str, str | list[str]] | None = None
    sections: list[dict[str, str | list[str]]] = []

    for line in lines:
        if line.strip() == "## 正文":
            in_body = True
            continue
        if in_body and line.startswith("## "):
            break
        if not in_body:
            continue

        match = SECTION_RE.match(line)
        if match:
            if current:
                sections.append(current)
            current = {"id": match.group(1), "title": match.group(2), "lines": []}
            continue

        if current is not None:
            stripped = line.strip()
            if stripped:
                current["lines"].append(stripped)

    if current:
        sections.append(current)

    return [
        {
            "id": str(section["id"]),
            "title": str(section["title"]),
            "text": "\n".join(section["lines"]),
        }
        for section in sections
    ]


def speed_up_audio(input_path: Path, output_path: Path, speed: float) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(input_path),
            "-filter:a",
            f"atempo={speed}",
            str(output_path),
        ],
        check=True,
    )


def audio_duration(path: Path) -> float:
    info = sf.info(path)
    return round(info.frames / info.samplerate, 3)


def main() -> None:
    args = parse_args()
    script_path = Path(args.script)
    output_dir = Path(args.output_dir)
    raw_dir = output_dir / "raw"
    label = speed_label(args.speed)
    speed_dir = output_dir / label
    raw_dir.mkdir(parents=True, exist_ok=True)
    speed_dir.mkdir(parents=True, exist_ok=True)

    sections = extract_sections(script_path)
    if not sections:
        raise RuntimeError(f"No Sxx sections found in {script_path}")

    model = VoxCPM.from_pretrained(
        args.model,
        load_denoiser=args.load_denoiser,
        cache_dir=args.cache_dir,
        device=args.device,
    )

    manifest = {
        "script": str(script_path),
        "reference_wav": args.reference_wav,
        "speed": args.speed,
        "sections": [],
    }

    sample_rate = getattr(getattr(model, "tts_model", None), "sample_rate", 48000)

    for index, section in enumerate(sections, start=1):
        base_name = f"{section['id']}_{section['title']}"
        safe_name = re.sub(r'[<>:"/\\|?*\s]+', "_", base_name).strip("_")
        raw_path = raw_dir / f"{safe_name}.wav"
        speed_path = speed_dir / f"{safe_name}_{label}.wav"

        print(f"[{index}/{len(sections)}] Generating {section['id']} {section['title']}")
        wav = model.generate(
            text=section["text"],
            reference_wav_path=args.reference_wav,
            cfg_value=args.cfg_value,
            inference_timesteps=args.timesteps,
        )
        sf.write(raw_path, wav, sample_rate)
        speed_up_audio(raw_path, speed_path, args.speed)

        manifest["sections"].append(
            {
                "id": section["id"],
                "title": section["title"],
                "text_chars": len(section["text"]),
                "raw_path": str(raw_path),
                "raw_duration": audio_duration(raw_path),
                "speed_path": str(speed_path),
                "speed_duration": audio_duration(speed_path),
            }
        )

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    total_raw = round(sum(item["raw_duration"] for item in manifest["sections"]), 3)
    total_speed = round(sum(item["speed_duration"] for item in manifest["sections"]), 3)
    print(f"Wrote manifest: {manifest_path}")
    print(f"Total raw duration: {total_raw}s")
    print(f"Total speed duration: {total_speed}s")


if __name__ == "__main__":
    main()
