from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

WIDTH = 1080
HEIGHT = 1920
FPS = 30


def run_ffmpeg(args: list[str]) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg was not found on PATH. Install FFmpeg and run this again.")

    result = subprocess.run([ffmpeg, *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-4000:])


def find_font() -> Path:
    """Find a standard Windows font without requiring a Fontconfig installation."""
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
        Path(r"C:\Windows\Fonts\calibri.ttf"),
    ]
    for font in candidates:
        if font.is_file():
            return font
    raise RuntimeError(
        "No usable Windows font was found. Expected Arial, Segoe UI, or Calibri "
        "under C:\\Windows\\Fonts."
    )


def ffmpeg_filter_path(path: Path) -> str:
    """Escape a Windows font path for FFmpeg's filter syntax."""
    return str(path).replace("\\", "/").replace(":", r"\:")


def make_test_scene(output: Path) -> None:
    """Render a GPU-free starter meme video using FFmpeg's built-in filters."""
    output.parent.mkdir(parents=True, exist_ok=True)
    fontfile = ffmpeg_filter_path(find_font())

    # Explicit fontfile avoids FFmpeg trying to initialize Fontconfig on Windows.
    filter_graph = (
        f"color=c=black:s={WIDTH}x{HEIGHT}:r={FPS}:d=8,"
        f"drawtext=fontfile='{fontfile}':text='MONEY BOT TEST':"
        "fontcolor=white:fontsize=82:"
        "x=(w-text_w)/2:y=(h-text_h)/2"
    )

    run_ffmpeg([
        "-y",
        "-f", "lavfi",
        "-i", filter_graph,
        "-t", "8",
        "-an",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output),
    ])


def render_from_scene(scene_path: Path, output: Path) -> None:
    """Validate a scene JSON before asset-based rendering is enabled."""
    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    if not isinstance(scene, dict):
        raise ValueError("Scene JSON must contain an object.")

    shots = scene.get("shots")
    if not isinstance(shots, list) or not shots:
        raise ValueError("Scene JSON must contain a non-empty 'shots' list.")

    for index, shot in enumerate(shots, 1):
        if not isinstance(shot, dict):
            raise ValueError(f"Shot {index} must be an object.")
        duration = shot.get("duration")
        if not isinstance(duration, (int, float)) or duration <= 0:
            raise ValueError(f"Shot {index} needs a positive numeric duration.")

    raise NotImplementedError(
        "Asset-based scene rendering is the next renderer stage. "
        "The test renderer is ready; external assets are not required yet."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="GPU-free FFmpeg meme video renderer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    test_parser = subparsers.add_parser("test", help="render an 8-second renderer test")
    test_parser.add_argument("--output", type=Path, default=Path("content") / "renderer_test.mp4")

    scene_parser = subparsers.add_parser("scene", help="validate/render a scene JSON")
    scene_parser.add_argument("scene", type=Path)
    scene_parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()

    if args.command == "test":
        make_test_scene(args.output)
        print(f"Created renderer test: {args.output}")
    else:
        render_from_scene(args.scene, args.output)


if __name__ == "__main__":
    main()
