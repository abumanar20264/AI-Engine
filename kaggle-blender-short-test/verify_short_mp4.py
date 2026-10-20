import argparse
import hashlib
import json
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

import av
from PIL import Image, ImageChops, ImageDraw, ImageStat


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rate_value(value):
    return float(value) if value is not None else None


def stream_duration(stream):
    if stream.duration is None or stream.time_base is None:
        return None
    return float(stream.duration * stream.time_base)


def main():
    parser = argparse.ArgumentParser(description="Inspect and fully decode a rendered MP4.")
    parser.add_argument("video", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    video = args.video.resolve(strict=True)
    output_dir = args.output_dir.resolve()
    if not video.is_file() or video.stat().st_size == 0:
        raise ValueError(f"Video must be a non-empty file: {video}")
    output_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "video": {
            "path": str(video),
            "size_bytes": video.stat().st_size,
            "sha256": sha256_file(video),
        },
        "status": "FAILED",
        "errors": [],
        "extracted_frames": [],
    }

    samples = {0, 59, 119}
    sample_images = {}
    decoded_frame_count = 0
    try:
        with av.open(str(video), mode="r") as container:
            video_streams = [stream for stream in container.streams if stream.type == "video"]
            audio_streams = [stream for stream in container.streams if stream.type == "audio"]
            if not video_streams:
                raise ValueError("MP4 contains no video stream.")
            stream = video_streams[0]
            stream_rate = stream.average_rate or stream.base_rate or stream.guessed_rate
            duration_seconds = (
                float(container.duration / av.time_base)
                if container.duration is not None
                else stream_duration(stream)
            )
            report["container"] = {
                "format_name": container.format.name,
                "duration_seconds": duration_seconds,
                "bit_rate": container.bit_rate,
            }
            report["video_stream"] = {
                "codec": stream.codec_context.name,
                "width": stream.codec_context.width,
                "height": stream.codec_context.height,
                "frame_rate": str(stream_rate) if stream_rate is not None else None,
                "frame_rate_float": rate_value(stream_rate),
                "average_rate": str(stream.average_rate) if stream.average_rate is not None else None,
                "time_base": str(stream.time_base) if stream.time_base is not None else None,
                "duration_seconds": stream_duration(stream),
                "declared_frame_count": stream.frames or None,
            }
            report["audio_streams"] = [
                {
                    "codec": audio.codec_context.name,
                    "duration_seconds": stream_duration(audio),
                    "sample_rate": audio.codec_context.sample_rate,
                    "channels": audio.codec_context.channels,
                }
                for audio in audio_streams
            ]

            for frame in container.decode(stream):
                if frame.width != stream.codec_context.width or frame.height != stream.codec_context.height:
                    raise ValueError(
                        f"Decoded frame {decoded_frame_count} dimensions changed to "
                        f"{frame.width}x{frame.height}."
                    )
                if decoded_frame_count in samples:
                    sample_images[decoded_frame_count] = frame.to_image().convert("RGB")
                decoded_frame_count += 1

        report["decoded_frame_count"] = decoded_frame_count
        for index, image in sample_images.items():
            frame_path = output_dir / f"mp4_verified_frame_{index + 1:04d}.png"
            image.save(frame_path, format="PNG")
            report["extracted_frames"].append({
                "frame_index_zero_based": index,
                "path": str(frame_path),
                "size_bytes": frame_path.stat().st_size,
                "sha256": sha256_file(frame_path),
            })

        motion_differences = {}
        for left, right in ((0, 59), (59, 119), (0, 119)):
            if left in sample_images and right in sample_images:
                delta = ImageChops.difference(sample_images[left], sample_images[right])
                motion_differences[f"{left}-{right}"] = round(
                    sum(ImageStat.Stat(delta).mean) / 3, 4
                )
        report["sampled_frame_mean_absolute_differences"] = motion_differences
        report["visible_motion_detected"] = bool(
            motion_differences and max(motion_differences.values()) > 3.0
        )

        if len(sample_images) == len(samples):
            frame_width = 320
            frame_height = round(frame_width * 16 / 9)
            tile_height = frame_height + 28
            contact_sheet = Image.new("RGB", (frame_width * 3, tile_height), "white")
            draw = ImageDraw.Draw(contact_sheet)
            for column, index in enumerate((0, 59, 119)):
                image = sample_images[index].resize((frame_width, frame_height))
                x = column * frame_width
                contact_sheet.paste(image, (x, 28))
                draw.text((x + 8, 7), f"Frame {index + 1}", fill="black")
            contact_path = output_dir / "mp4_verified_contact_sheet.png"
            contact_sheet.save(contact_path, format="PNG")
            report["contact_sheet"] = {
                "path": str(contact_path),
                "size_bytes": contact_path.stat().st_size,
                "sha256": sha256_file(contact_path),
            }

        format_names = set(report["container"]["format_name"].split(","))
        checks = {
            "mp4_container": "mp4" in format_names,
            "h264_video": report["video_stream"]["codec"] == "h264",
            "resolution_720x1280": (
                report["video_stream"]["width"],
                report["video_stream"]["height"],
            ) == (720, 1280),
            "frame_rate_24": (
                report["video_stream"]["frame_rate_float"] is not None
                and abs(report["video_stream"]["frame_rate_float"] - 24.0) < 0.01
            ),
            "frame_count_120": decoded_frame_count == 120,
            "duration_about_5_seconds": (
                duration_seconds is not None and 4.95 <= duration_seconds <= 5.05
            ),
            "full_video_decode": decoded_frame_count > 0,
            "first_middle_last_frames_extracted": len(sample_images) == len(samples),
            "visible_motion_detected": report["visible_motion_detected"],
        }
        report["checks"] = checks
        report["status"] = "VERIFIED" if all(checks.values()) else "FAILED"
        if report["status"] == "FAILED":
            report["errors"].append(
                "One or more acceptance checks failed: "
                + ", ".join(name for name, passed in checks.items() if not passed)
            )
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        report["decode_error"] = f"{type(exc).__name__}: {exc}"

    report["completed_utc"] = datetime.now(timezone.utc).isoformat()
    report_path = output_dir / "mp4_verification_report.json"
    report["report_path"] = str(report_path)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
