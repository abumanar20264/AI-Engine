"""Validate rendered video artifacts against a saved project and task."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any

from .project_store import validate_project


class VideoArtifactError(RuntimeError):
    """Raised when a rendered video cannot be verified for its task."""


def verify_video_artifact(
    video_path: str | Path,
    project: dict[str, Any],
    task_id: str,
    *,
    ffmpeg: str | None = None,
    ffprobe: str | None = None,
) -> dict[str, Any]:
    normalized = validate_project(project)
    if normalized["audio"]["enabled"]:
        raise VideoArtifactError(
            "This render pipeline does not produce audio; disable required audio before submitting."
        )
    path = Path(video_path)
    if not path.is_file() or path.stat().st_size == 0:
        raise VideoArtifactError("Rendered MP4 is missing or empty.")
    ffmpeg_path = ffmpeg or shutil.which("ffmpeg")
    ffprobe_path = ffprobe or shutil.which("ffprobe")
    if not ffmpeg_path or not ffprobe_path:
        raise VideoArtifactError("ffmpeg and ffprobe are required to validate rendered video.")

    probe = _run(
        [
            ffprobe_path,
            "-v", "error",
            "-show_entries",
            "stream=codec_type,codec_name,width,height,avg_frame_rate,nb_frames,duration",
            "-show_entries", "format=duration,size",
            "-of", "json",
            str(path),
        ],
        "ffprobe metadata validation",
    )
    try:
        metadata = json.loads(probe.stdout)
    except json.JSONDecodeError as exc:
        raise VideoArtifactError("ffprobe returned invalid JSON metadata.") from exc
    streams = metadata.get("streams")
    if not isinstance(streams, list):
        raise VideoArtifactError("ffprobe returned no stream list.")
    video_streams = [item for item in streams if item.get("codec_type") == "video"]
    audio_streams = [item for item in streams if item.get("codec_type") == "audio"]
    if len(video_streams) != 1:
        raise VideoArtifactError("MP4 must contain exactly one video stream.")
    if audio_streams:
        raise VideoArtifactError("Unexpected audio stream; audio muxing is not supported yet.")
    stream = video_streams[0]
    settings = normalized["scenario"]["video"]
    try:
        frame_rate_matches = (
            Fraction(stream["avg_frame_rate"]) == Fraction(settings["fps"], 1)
        )
        frame_count = int(stream["nb_frames"])
        duration = float(stream.get("duration", metadata.get("format", {}).get("duration", 0)))
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        raise VideoArtifactError("MP4 metadata is incomplete or invalid.") from exc
    expected_duration = settings["frame_count"] / settings["fps"]
    tolerance = max(0.01, 0.51 / settings["fps"])
    checks = {
        "h264_codec": stream.get("codec_name") == "h264",
        "resolution_matches_project": (
            stream.get("width"), stream.get("height")
        ) == (settings["width"], settings["height"]),
        "frame_rate_matches_project": frame_rate_matches,
        "frame_count_matches_project": frame_count == settings["frame_count"],
        "duration_matches_project": abs(duration - expected_duration) <= tolerance,
    }
    if not all(checks.values()):
        failed = ", ".join(name for name, passed in checks.items() if not passed)
        raise VideoArtifactError(f"MP4 does not match project video settings: {failed}.")

    _run(
        [ffmpeg_path, "-v", "error", "-i", str(path), "-f", "null", "-"],
        "full MP4 decode",
    )
    checks["full_decode"] = True
    middle_frame = settings["frame_count"] // 2
    last_frame = settings["frame_count"] - 1
    motion = _run(
        [
            ffmpeg_path,
            "-v", "error", "-i", str(path),
            "-vf", f"select='eq(n,0)+eq(n,{middle_frame})+eq(n,{last_frame})',scale=64:64",
            "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ],
        "visible motion validation",
    )
    frame_bytes = 64 * 64 * 3
    decoded_count = len(motion.stdout) // frame_bytes
    frames = [
        motion.stdout[index * frame_bytes:(index + 1) * frame_bytes]
        for index in range(decoded_count)
    ]
    differences = [
        sum(abs(left - right) for left, right in zip(frames[0], frames[index]))
        / frame_bytes
        for index in range(1, len(frames))
    ] if decoded_count == 3 else []
    checks["visible_motion"] = bool(differences and max(differences) > 3.0)
    if not checks["visible_motion"]:
        raise VideoArtifactError("MP4 did not show measurable motion across sampled frames.")

    digest = hashlib.sha256()
    with path.open("rb") as video_file:
        for chunk in iter(lambda: video_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "schema_version": 1,
        "status": "PASSED",
        "task_id": task_id,
        "project_id": normalized["id"],
        "video_file": str(path.resolve()),
        "size_bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
        "metadata": {
            "codec": stream["codec_name"],
            "width": stream["width"],
            "height": stream["height"],
            "fps": settings["fps"],
            "frame_count": frame_count,
            "duration_seconds": duration,
        },
        "checks": checks,
        "audio": {"status": "NOT_AVAILABLE", "reason": "Audio rendering is not implemented."},
    }


def validate_video_evidence(
    evidence: object,
    project: dict[str, Any],
    task_id: str,
    kernel_version: str,
) -> dict[str, Any]:
    normalized = validate_project(project)
    if normalized["audio"]["enabled"]:
        raise VideoArtifactError("Project requires audio, but no audio artifact is available.")
    if not isinstance(evidence, dict):
        raise VideoArtifactError("Kaggle report is missing video verification evidence.")
    checks = evidence.get("checks")
    required_checks = {
        "h264_codec",
        "resolution_matches_project",
        "frame_rate_matches_project",
        "frame_count_matches_project",
        "duration_matches_project",
        "full_decode",
        "visible_motion",
    }
    metadata = evidence.get("metadata")
    audio = evidence.get("audio")
    settings = normalized["scenario"]["video"]
    expected_duration = settings["frame_count"] / settings["fps"]
    if (
        evidence.get("schema_version") != 1
        or evidence.get("status") != "PASSED"
        or evidence.get("task_id") != task_id
        or evidence.get("project_id") != normalized["id"]
        or evidence.get("kaggle_kernel_slug") != "haroonbaaraabumanar/ai-engine-blender-runtime-preflight"
        or evidence.get("kaggle_kernel_version") != kernel_version
        or not isinstance(evidence.get("video_file"), str)
        or Path(evidence["video_file"]).name != f"{normalized['id']}.mp4"
        or not isinstance(evidence.get("size_bytes"), int)
        or isinstance(evidence.get("size_bytes"), bool)
        or evidence["size_bytes"] <= 0
        or not isinstance(evidence.get("sha256"), str)
        or len(evidence["sha256"]) != 64
        or any(character not in "0123456789abcdef" for character in evidence["sha256"])
        or not isinstance(metadata, dict)
        or metadata.get("codec") != "h264"
        or metadata.get("width") != settings["width"]
        or metadata.get("height") != settings["height"]
        or metadata.get("fps") != settings["fps"]
        or metadata.get("frame_count") != settings["frame_count"]
        or not isinstance(metadata.get("duration_seconds"), (int, float))
        or not math.isfinite(metadata.get("duration_seconds", float("nan")))
        or abs(metadata["duration_seconds"] - expected_duration)
        > max(0.01, 0.51 / settings["fps"])
        or not isinstance(checks, dict)
        or not required_checks.issubset(checks)
        or not all(checks[name] is True for name in required_checks)
        or not isinstance(audio, dict)
        or audio.get("status") != "NOT_AVAILABLE"
    ):
        raise VideoArtifactError("Video verification evidence failed identity or acceptance checks.")
    return evidence


def _run(command: list[str], operation: str) -> subprocess.CompletedProcess[bytes]:
    try:
        result = subprocess.run(command, check=False, capture_output=True, timeout=600)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VideoArtifactError(f"{operation} could not complete: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.decode(errors="replace")[-2000:]
        raise VideoArtifactError(f"{operation} failed: {detail or result.returncode}")
    return result