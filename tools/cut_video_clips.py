#!/usr/bin/env python3
"""Cut reference clips from the Miyazaki documentary."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import av


@dataclass(frozen=True)
class ClipSpec:
    name: str
    episode: int
    start: str
    end: str


EPISODES = {
    1: "10 Years with Hayao Miyazaki - Episode 01 - Ponyo is Here 1080p BDRip x265 FLAC 2.0 Kira [SEV].mkv",
    2: "10 Years with Hayao Miyazaki - Episode 02 - Drawing What's Real 1080p BDRip x265 FLAC 2.0 Kira [SEV].mkv",
    3: "10 Years with Hayao Miyazaki - Episode 03 - Go Ahead - Threaten Me 1080p BDRip x265 FLAC 2.0 Kira [SEV].mkv",
    4: "10 Years with Hayao Miyazaki - Episode 04 - No Cheap Excuses 1080p BDRip x265 FLAC 2.0 Kira [SEV].mkv",
}

CORE_CLIPS = [
    ClipSpec("S01_EP01_0027_0141_studio_arrival", 1, "00:27", "01:41"),
    ClipSpec("S04_EP01_0845_0959_no_script_image_board", 1, "08:45", "09:59"),
    ClipSpec("S04_EP01_1307_1342_first_image_flows", 1, "13:07", "13:42"),
    ClipSpec("S04_EP01_1351_1448_throw_away_opening", 1, "13:51", "14:48"),
    ClipSpec("S06_EP01_2352_2757_pastel_simple_lines", 1, "23:52", "27:57"),
    ClipSpec("S06_EP02_0203_0216_no_cg_hand_drawn", 2, "02:03", "02:16"),
    ClipSpec("S07_EP02_0440_0642_redraw_ponyo_emotion", 2, "04:40", "06:42"),
    ClipSpec("S08_EP01_3539_3935_seto_inland_sea_life", 1, "35:39", "39:35"),
    ClipSpec("S08_EP02_0816_1028_real_child_three_meter", 2, "08:16", "10:28"),
    ClipSpec("S09_EP02_4202_4659_toki_hug_memory", 2, "42:02", "46:59"),
    ClipSpec("S11_EP04_2007_2138_age_toll", 4, "20:07", "21:38"),
    ClipSpec("S13_EP04_4006_4137_naoko_folds_shirt", 4, "40:06", "41:37"),
]

BROLL_CLIPS = [
    ClipSpec("BROLL_EP01_0244_0259_starts_drawing", 1, "02:44", "02:59"),
    ClipSpec("BROLL_EP01_0420_0443_sketch_wall", 1, "04:20", "04:43"),
    ClipSpec("BROLL_EP01_2056_2136_style_realization", 1, "20:56", "21:36"),
    ClipSpec("BROLL_EP01_3550_3615_sea_arrival", 1, "35:50", "36:15"),
    ClipSpec("BROLL_EP01_3639_3723_seaside_walk_life", 1, "36:39", "37:23"),
    ClipSpec("BROLL_EP01_3755_3935_sea_life_empty_shots", 1, "37:55", "39:35"),
    ClipSpec("BROLL_EP01_4212_4325_pencil_storyboard", 1, "42:12", "43:25"),
    ClipSpec("BROLL_EP02_0320_0350_gesture_direction", 2, "03:20", "03:50"),
    ClipSpec("BROLL_EP02_0816_0945_real_child_fuki", 2, "08:16", "09:45"),
    ClipSpec("BROLL_EP02_1003_1028_three_meter_radius", 2, "10:03", "10:28"),
    ClipSpec("BROLL_EP02_4202_4308_toki_stands", 2, "42:02", "43:08"),
    ClipSpec("BROLL_EP02_4402_4659_toki_hug", 2, "44:02", "46:59"),
]

ALL_CLIPS = CORE_CLIPS + BROLL_CLIPS


def parse_time(value: str) -> float:
    parts = [float(part) for part in value.split(":")]
    if len(parts) == 2:
        minutes, seconds = parts
        return minutes * 60 + seconds
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return hours * 3600 + minutes * 60 + seconds
    raise ValueError(f"Invalid timestamp: {value}")


def cut_clip(input_path: Path, output_path: Path, start: float, end: float) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with av.open(str(input_path)) as source:
        streams = [
            stream
            for stream in source.streams
            if stream.type in {"video", "audio"}
        ]
        if not streams:
            raise RuntimeError(f"No video/audio streams found: {input_path}")

        with av.open(str(output_path), mode="w", format="matroska") as target:
            stream_map = {}
            for in_stream in streams:
                out_stream = target.add_stream_from_template(in_stream)
                stream_map[in_stream.index] = out_stream

            # Stream-copy cuts must begin on a keyframe. Seeking backward may include
            # a few seconds before the requested start, but keeps the clip playable.
            source.seek(int(start * av.time_base), backward=True, any_frame=False)
            first_pts_by_stream: dict[int, int] = {}
            first_dts_by_stream: dict[int, int] = {}
            for packet in source.demux(streams):
                if packet.dts is None:
                    continue
                packet_time = float(packet.dts * packet.time_base)
                if packet_time > end:
                    break
                if packet.pts is not None:
                    first_pts_by_stream.setdefault(packet.stream.index, packet.pts)
                    packet.pts -= first_pts_by_stream[packet.stream.index]
                if packet.dts is not None:
                    first_dts_by_stream.setdefault(packet.stream.index, packet.dts)
                    packet.dts -= first_dts_by_stream[packet.stream.index]
                packet.stream = stream_map[packet.stream.index]
                target.mux(packet)


def even(value: int) -> int:
    return value if value % 2 == 0 else value - 1


def cut_video_only(
    input_path: Path,
    output_path: Path,
    start: float,
    end: float,
    width: int,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with av.open(str(input_path)) as source:
        in_stream = source.streams.video[0]
        rate = in_stream.average_rate or 24
        src_width = in_stream.codec_context.width
        src_height = in_stream.codec_context.height
        height = even(round(src_height * width / src_width))

        with av.open(str(output_path), mode="w", format="matroska") as target:
            out_stream = target.add_stream("libx264", rate=rate)
            out_stream.width = width
            out_stream.height = height
            out_stream.pix_fmt = "yuv420p"
            out_stream.time_base = Fraction(1, 1000)
            out_stream.options = {"preset": "veryfast", "crf": "23", "tune": "zerolatency"}

            source.seek(int(start * av.time_base), backward=True, any_frame=False)
            frame_index = 0
            for frame in source.decode(in_stream):
                if frame.pts is None:
                    continue
                frame_time = float(frame.pts * in_stream.time_base)
                if frame_time < start:
                    continue
                if frame_time > end:
                    break

                frame = frame.reformat(width=width, height=height, format="yuv420p")
                seconds_per_frame = (
                    rate.denominator / rate.numerator
                    if isinstance(rate, Fraction)
                    else 1 / float(rate)
                )
                frame.pts = int(round(frame_index * seconds_per_frame * 1000))
                frame.time_base = Fraction(1, 1000)
                frame_index += 1
                for packet in out_stream.encode(frame):
                    target.mux(packet)

            for packet in out_stream.encode():
                target.mux(packet)


def main() -> int:
    parser = argparse.ArgumentParser(description="Cut core Miyazaki reference clips.")
    parser.add_argument("source_dir", help="Folder containing the four documentary MKV files.")
    parser.add_argument("--output-dir", default="video_clips/miyazaki_first_video")
    parser.add_argument("--only", help="Cut one clip by name.")
    parser.add_argument(
        "--set",
        choices=["core", "broll", "all"],
        default="core",
        help="Choose which clip set to cut.",
    )
    parser.add_argument(
        "--mode",
        choices=["video-only", "streamcopy"],
        default="video-only",
        help="video-only creates 720p MP4 clips; streamcopy tries MKV without re-encoding.",
    )
    parser.add_argument("--width", type=int, default=1280, help="Output width for video-only mode.")
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    output_dir = Path(args.output_dir)
    specs = {"core": CORE_CLIPS, "broll": BROLL_CLIPS, "all": ALL_CLIPS}[args.set]
    if args.only:
        specs = [clip for clip in ALL_CLIPS if clip.name == args.only]
        if not specs:
            raise SystemExit(f"Unknown clip name: {args.only}")

    for clip in specs:
        input_path = source_dir / EPISODES[clip.episode]
        suffix = ".mkv"
        output_path = output_dir / f"{clip.name}{suffix}"
        print(f"cutting {clip.name} -> {output_path}")
        if args.mode == "video-only":
            cut_video_only(
                input_path=input_path,
                output_path=output_path,
                start=parse_time(clip.start),
                end=parse_time(clip.end),
                width=args.width,
            )
        else:
            cut_clip(
                input_path=input_path,
                output_path=output_path,
                start=parse_time(clip.start),
                end=parse_time(clip.end),
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
