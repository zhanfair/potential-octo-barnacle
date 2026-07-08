from __future__ import annotations

import argparse
from pathlib import Path

import soundfile as sf
from voxcpm import VoxCPM


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a minimal VoxCPM Chinese TTS test.")
    parser.add_argument(
        "--text",
        default="\u8fd9\u662f VoxCPM \u7684\u672c\u5730\u8bed\u97f3\u5408\u6210\u6d4b\u8bd5\u3002\u5982\u679c\u4f60\u542c\u5230\u8fd9\u53e5\u8bdd\uff0c\u8bf4\u660e\u73af\u5883\u5df2\u7ecf\u8dd1\u901a\u4e86\u3002",
    )
    parser.add_argument("--output", default="voice_outputs/voxcpm_smoke_test.wav")
    parser.add_argument("--cache-dir", default="pretrained_models")
    parser.add_argument("--model", default="openbmb/VoxCPM2")
    parser.add_argument("--device", default=None)
    parser.add_argument("--reference-wav", default=None)
    parser.add_argument("--prompt-wav", default=None)
    parser.add_argument("--prompt-text", default=None)
    parser.add_argument("--cfg-value", type=float, default=2.0)
    parser.add_argument("--timesteps", type=int, default=10)
    parser.add_argument("--load-denoiser", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    model = VoxCPM.from_pretrained(
        args.model,
        load_denoiser=args.load_denoiser,
        cache_dir=str(cache_dir),
        device=args.device,
    )

    generate_kwargs = {
        "text": args.text,
        "cfg_value": args.cfg_value,
        "inference_timesteps": args.timesteps,
    }
    if args.reference_wav:
        generate_kwargs["reference_wav_path"] = args.reference_wav
    if args.prompt_wav:
        generate_kwargs["prompt_wav_path"] = args.prompt_wav
    if args.prompt_text:
        generate_kwargs["prompt_text"] = args.prompt_text

    wav = model.generate(**generate_kwargs)
    sample_rate = getattr(getattr(model, "tts_model", None), "sample_rate", 48000)
    sf.write(output_path, wav, sample_rate)
    print(f"Wrote {output_path} at {sample_rate} Hz")


if __name__ == "__main__":
    main()
