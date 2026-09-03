from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

WIDTH = 1080
HEIGHT = 1920
FPS = 30
ASSET_ROOT = Path("assets")


def run_ffmpeg(args: list[str]) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg was not found on PATH. Install FFmpeg and run this again.")
    result = subprocess.run([ffmpeg, *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-4000:])


def find_font() -> Path:
    """Find a standard Windows font without requiring Fontconfig."""
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
        Path(r"C:\Windows\Fonts\calibri.ttf"),
    ]
    for font in candidates:
        if font.is_file():
            return font
    raise RuntimeError("No usable Windows font found under C:\\Windows\\Fonts.")


def ffmpeg_filter_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace(":", r"\:")


def ffmpeg_input_path(path: Path) -> str:
    return str(path.resolve())


def make_test_scene(output: Path) -> None:
    """Render an 8-second GPU-free renderer test."""
    output.parent.mkdir(parents=True, exist_ok=True)
    fontfile = ffmpeg_filter_path(find_font())
    filter_graph = (
        f"color=c=black:s={WIDTH}x{HEIGHT}:r={FPS}:d=8,"
        f"drawtext=fontfile='{fontfile}':text='MONEY BOT TEST':"
        "fontcolor=white:fontsize=82:x=(w-text_w)/2:y=(h-text_h)/2"
    )
    run_ffmpeg([
        "-y", "-f", "lavfi", "-i", filter_graph, "-t", "8", "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output),
    ])


def resolve_asset(value: str, category: str) -> Path:
    """Resolve an asset relative to the repository's assets directory."""
    raw = Path(value)
    candidates = [raw, ASSET_ROOT / category / raw]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Asset not found: {value} (looked in assets/{category}/)")


def render_image_shot(
    image: Path,
    duration: float,
    output: Path,
    caption: str | None = None,
    zoom: float = 1.0,
    position: str = "center",
) -> None:
    """Render one image into a 9:16 MP4 shot with optional caption and slow zoom."""
    output.parent.mkdir(parents=True, exist_ok=True)
    fontfile = ffmpeg_filter_path(find_font())
    escaped_caption = (caption or "").replace("\\", r"\\").replace(":", r"\:").replace("'", r"\\'")

    filters = [
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase",
        f"crop={WIDTH}:{HEIGHT}",
    ]
    if zoom > 1.0:
        filters.append(
            f"zoompan=z='min(zoom+{(zoom - 1.0) / max(duration * FPS, 1):.8f},{zoom:.4f})':"
            f"d=1:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    if caption:
        # Captions are deliberately the only generated text layer. No dialogue or
        # voiceover is required; supplied audio is handled separately later.
        filters.append(
            f"drawtext=fontfile='{fontfile}':text='{escaped_caption}':"
            "fontcolor=white:fontsize=64:borderw=5:bordercolor=black:"
            "x=(w-text_w)/2:y=h*0.78"
        )

    run_ffmpeg([
        "-y", "-loop", "1", "-i", ffmpeg_input_path(image),
        "-t", str(duration), "-vf", ",".join(filters), "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output),
    ])


def concat_shots(shots: list[Path], output: Path) -> None:
    """Concatenate rendered shots without requiring audio."""
    output.parent.mkdir(parents=True, exist_ok=True)
    list_file = output.with_suffix(".concat.txt")
    list_file.write_text(
        "".join(f"file '{shot.resolve().as_posix().replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'\n" for shot in shots),
        encoding="utf-8",
    )
    try:
        run_ffmpeg([
            "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-an", "-c", "copy", "-movflags", "+faststart", str(output),
        ])
    finally:
        list_file.unlink(missing_ok=True)


def render_from_scene(scene_path: Path, output: Path) -> None:
    """Render an asset-based scene JSON into a silent vertical MP4."""
    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    if not isinstance(scene, dict):
        raise ValueError("Scene JSON must contain an object.")

    shots = scene.get("shots")
    if not isinstance(shots, list) or not shots:
        raise ValueError("Scene JSON must contain a non-empty 'shots' list.")

    work_dir = output.parent / f".{output.stem}_shots"
    work_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []
    try:
        for index, shot in enumerate(shots, 1):
            if not isinstance(shot, dict):
                raise ValueError(f"Shot {index} must be an object.")
            duration = shot.get("duration")
            if not isinstance(duration, (int, float)) or duration <= 0:
                raise ValueError(f"Shot {index} needs a positive numeric duration.")
            image_value = shot.get("image") or shot.get("background")
            if not isinstance(image_value, str) or not image_value.strip():
                raise ValueError(f"Shot {index} needs an 'image' or 'background' asset path.")
            category = "backgrounds" if shot.get("background") else "characters"
            image = resolve_asset(image_value, category)
            caption = shot.get("caption")
            if caption is not None and not isinstance(caption, str):
                raise ValueError(f"Shot {index} caption must be a string or null.")
            zoom = shot.get("zoom", 1.0)
            if not isinstance(zoom, (int, float)) or zoom < 1.0 or zoom > 1.25:
                raise ValueError(f"Shot {index} zoom must be between 1.0 and 1.25.")

            shot_output = work_dir / f"shot_{index:03d}.mp4"
            render_image_shot(image, float(duration), shot_output, caption, float(zoom))
            rendered.append(shot_output)

        concat_shots(rendered, output)
        print(f"Created video: {output}")
        print("Audio: not required. Add your own audio separately when desired.")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="GPU-free FFmpeg meme video renderer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    test_parser = subparsers.add_parser("test", help="render an 8-second renderer test")
    test_parser.add_argument("--output", type=Path, default=Path("content") / "renderer_test.mp4")

    scene_parser = subparsers.add_parser("scene", help="render an asset-based scene JSON")
    scene_parser.add_argument("scene", type=Path)
    scene_parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "test":
        make_test_scene(args.output)
    else:
        render_from_scene(args.scene, args.output)


if __name__ == "__main__":
    main()
