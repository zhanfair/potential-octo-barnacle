from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg
import soundfile as sf


SECTION_RE = re.compile(r"^###\s+(S\d{2})\s+(.+?)\s*$")

CLIP_MAP = {
    "S01": "S01_EP01_0027_0141_studio_arrival.mkv",
    "S02": "S01_EP01_0027_0141_studio_arrival.mkv",
    "S03": "S04_EP01_0845_0959_no_script_image_board.mkv",
    "S04": "S04_EP01_0845_0959_no_script_image_board.mkv",
    "S05": "S04_EP01_1351_1448_throw_away_opening.mkv",
    "S06": "S06_EP01_2352_2757_pastel_simple_lines.mkv",
    "S07": "S07_EP02_0440_0642_redraw_ponyo_emotion.mkv",
    "S08": "S08_EP01_3539_3935_seto_inland_sea_life.mkv",
    "S09": "S09_EP02_4202_4659_toki_hug_memory.mkv",
    "S10": "S06_EP02_0203_0216_no_cg_hand_drawn.mkv",
    "S11": "S11_EP04_2007_2138_age_toll.mkv",
    "S12": "S04_EP01_1307_1342_first_image_flows.mkv",
    "S13": "S13_EP04_4006_4137_naoko_folds_shirt.mkv",
}

GOLD_LINES = {
    "S01": "不要用天才解释他",
    "S02": "普通人不是没想法",
    "S03": "想象力只是结果",
    "S04": "分镜是思考界面",
    "S05": "分镜也是行动地图",
    "S06": "手作是反馈链路",
    "S07": "情绪必须落到动作上",
    "S08": "现场是生命记忆库",
    "S09": "真实感不是画得像",
    "S10": "动作背后有没有人",
    "S11": "这不是温柔的方法",
    "S12": "先做出一个版本",
    "S13": "把雾逼成作品",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a rough watchable Miyazaki preview video.")
    parser.add_argument("--script", default="26_宫崎骏第一条视频完整口播稿.md")
    parser.add_argument("--audio-dir", default="voice_outputs/miyazaki_first_video/speed110")
    parser.add_argument("--full-audio", default="voice_outputs/miyazaki_first_video/miyazaki_first_video_full_speed110.wav")
    parser.add_argument("--clip-dir", default="video_clips/miyazaki_first_video")
    parser.add_argument("--output-dir", default="video_outputs/miyazaki_first_video_preview")
    parser.add_argument("--gap", type=float, default=0.35)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--band-height", type=int, default=608)
    return parser.parse_args()


def extract_sections(script_path: Path) -> list[dict[str, object]]:
    lines = script_path.read_text(encoding="utf-8").splitlines()
    in_body = False
    current: dict[str, object] | None = None
    sections: list[dict[str, object]] = []

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
        if current is not None and line.strip():
            current["lines"].append(line.strip())

    if current:
        sections.append(current)
    return sections


def audio_duration(path: Path) -> float:
    info = sf.info(path)
    return info.frames / info.samplerate


def find_audio(audio_dir: Path, section_id: str) -> Path:
    matches = sorted(audio_dir.glob(f"{section_id}_*_speed110.wav"))
    if not matches:
        raise FileNotFoundError(f"No audio segment found for {section_id}")
    return matches[0]


def ass_time(seconds: float) -> str:
    centiseconds = int(round(seconds * 100))
    hours, remainder = divmod(centiseconds, 360000)
    minutes, remainder = divmod(remainder, 6000)
    secs, centis = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def ass_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def chunk_lines(lines: list[str], max_chars: int = 22) -> list[str]:
    chunks: list[str] = []
    buffer = ""
    for line in lines:
        clean = line.strip()
        if not clean:
            continue
        if len(clean) > max_chars:
            if buffer:
                chunks.append(buffer)
                buffer = ""
            for start in range(0, len(clean), max_chars):
                chunks.append(clean[start : start + max_chars])
            continue
        candidate = clean if not buffer else f"{buffer}，{clean}"
        if len(candidate) <= max_chars:
            buffer = candidate
        else:
            chunks.append(buffer)
            buffer = clean
    if buffer:
        chunks.append(buffer)
    return chunks


def write_ass(sections: list[dict[str, object]], ass_path: Path, width: int, height: int) -> None:
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: White,Microsoft YaHei,58,&H00F4F4F4,&H000000FF,&H9A000000,&H7A000000,1,0,0,0,100,100,0,0,1,4,1,2,80,80,760,1
Style: Gold,Microsoft YaHei,78,&H0036C8FF,&H000000FF,&HCC000000,&H7A000000,1,0,0,0,100,100,0,0,1,5,1,8,80,80,620,1
Style: Title,Microsoft YaHei,34,&H00F0F0F0,&H000000FF,&H9A000000,&H7A000000,1,0,0,0,100,100,0,0,1,2,0,7,60,80,530,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events: list[str] = [header]
    cursor = 0.0
    for section in sections:
        section_id = str(section["id"])
        duration = float(section["duration"])
        section_end = cursor + duration
        gold = GOLD_LINES.get(section_id, str(section["title"]))

        events.append(
            f"Dialogue: 2,{ass_time(cursor)},{ass_time(min(cursor + 4.2, section_end))},Gold,,0,0,0,,{ass_escape(gold)}"
        )
        events.append(
            f"Dialogue: 1,{ass_time(cursor)},{ass_time(section_end)},Title,,0,0,0,,「宫崎骏的创作系统」"
        )

        chunks = chunk_lines(section["lines"])
        weights = [max(4, len(chunk)) for chunk in chunks]
        total_weight = sum(weights) or 1
        local = cursor + 1.0
        available = max(1.0, duration - 1.0)
        for chunk, weight in zip(chunks, weights):
            cue_duration = max(1.15, available * weight / total_weight)
            cue_end = min(section_end, local + cue_duration)
            if cue_end - local >= 0.45:
                events.append(
                    f"Dialogue: 3,{ass_time(local)},{ass_time(cue_end)},White,,0,0,0,,{ass_escape(chunk)}"
                )
            local = cue_end
            if local >= section_end:
                break
        cursor = section_end + float(section["gap"])

    ass_path.write_text("\n".join(events), encoding="utf-8")


def run(command: list[str]) -> None:
    print(" ".join(command))
    subprocess.run(command, check=True)


def render_segment(
    ffmpeg: str,
    clip_path: Path,
    output_path: Path,
    duration: float,
    width: int,
    height: int,
    band_height: int,
) -> None:
    y_offset = (height - band_height) // 2
    vf = (
        f"scale={width}:{band_height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{band_height},"
        "eq=brightness=-0.07:contrast=0.94:saturation=0.9,"
        f"pad={width}:{height}:0:{y_offset}:black,"
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
            "28",
            str(output_path),
        ]
    )


def main() -> None:
    args = parse_args()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    output_dir = Path(args.output_dir)
    segment_dir = output_dir / "segments"
    output_dir.mkdir(parents=True, exist_ok=True)
    segment_dir.mkdir(parents=True, exist_ok=True)

    sections = extract_sections(Path(args.script))
    for index, section in enumerate(sections):
        section_id = str(section["id"])
        audio_path = find_audio(Path(args.audio_dir), section_id)
        duration = audio_duration(audio_path)
        gap = args.gap if index < len(sections) - 1 else 0.0
        section["duration"] = duration
        section["gap"] = gap
        section["audio_path"] = str(audio_path)

        clip_name = CLIP_MAP[section_id]
        clip_path = Path(args.clip_dir) / clip_name
        segment_path = segment_dir / f"{section_id}.mp4"
        render_segment(
            ffmpeg=ffmpeg,
            clip_path=clip_path,
            output_path=segment_path,
            duration=duration + gap,
            width=args.width,
            height=args.height,
            band_height=args.band_height,
        )
        section["segment_path"] = str(segment_path)

    concat_path = output_dir / "concat.txt"
    concat_lines = [f"file '{Path(section['segment_path']).resolve().as_posix()}'" for section in sections]
    concat_path.write_text("\n".join(concat_lines), encoding="utf-8")

    base_path = output_dir / "miyazaki_preview_base.mp4"
    run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), "-c", "copy", str(base_path)])

    ass_path = output_dir / "miyazaki_preview_subtitles.ass"
    write_ass(sections, ass_path, args.width, args.height)

    final_path = output_dir / "miyazaki_first_video_preview_speed110.mp4"
    ass_filter_path = ass_path.as_posix().replace(":", "\\:")
    run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(base_path),
            "-i",
            args.full_audio,
            "-vf",
            f"ass='{ass_filter_path}'",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
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
