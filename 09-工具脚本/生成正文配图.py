from __future__ import annotations

import argparse
import time
from pathlib import Path

from PIL import Image, ImageOps

from ccswitch_image import REPO, generate_image


def parse_size(value: str) -> tuple[int, int]:
    width, height = value.lower().split("x", 1)
    return int(width), int(height)


def normalize_to_canvas(image_path: Path, canvas: tuple[int, int], safe_margin: int = 48) -> None:
    if safe_margin < 36 or safe_margin * 2 >= min(canvas):
        raise ValueError("safe_margin must be at least 36px and leave room for the visual")
    with Image.open(image_path) as image:
        inner = (canvas[0] - safe_margin * 2, canvas[1] - safe_margin * 2)
        normalized = ImageOps.contain(image.convert("RGB"), inner, method=Image.Resampling.LANCZOS)
        framed = Image.new("RGB", canvas, "#061226")
        x = (canvas[0] - normalized.width) // 2
        y = (canvas[1] - normalized.height) // 2
        framed.paste(normalized, (x, y))
        framed.save(image_path, format="PNG", optimize=True)


def append_record(article: str, output: Path, route: dict[str, str], prompt: str, canvas: tuple[int, int]) -> None:
    record = REPO / "07-资料与流程" / "图片生成记录.md"
    relative = output.relative_to(REPO).as_posix()
    record.parent.mkdir(parents=True, exist_ok=True)
    with record.open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n## {time.strftime('%Y-%m-%d %H:%M:%S')} - CC Switch 正文插图\n\n"
            f"- article: {article}\n"
            f"- route: {route['route']}\n"
            f"- endpoint: {route['endpoint']}\n"
            f"- image_tool: {route['image_tool']}\n"
            f"- response_model: {route['response_model']}\n"
            f"- image_model_selection: {route['image_model_selection']}\n"
            f"- quality: {route['quality']}\n"
            f"- output: {relative}\n"
            f"- canvas: {canvas[0]} x {canvas[1]}\n"
            f"- prompt: {prompt}\n"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a body visual through the local CC Switch Responses image route.")
    parser.add_argument("--article", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--canvas", default="1600x900")
    parser.add_argument("--api-size", default="1536x1024")
    parser.add_argument("--quality", default="high")
    parser.add_argument("--safe-margin", type=int, default=48)
    args = parser.parse_args()
    output = Path(args.output)
    if not output.is_absolute():
        output = (REPO / output).resolve()
    canvas = parse_size(args.canvas)
    route = generate_image(args.prompt, output, size=args.api_size, quality=args.quality)
    normalize_to_canvas(output, canvas, args.safe_margin)
    append_record(args.article, output, route, args.prompt, canvas)
    print(f"route={route['route']}")
    print(f"endpoint={route['endpoint']}")
    print(f"image_tool={route['image_tool']}")
    print(f"response_model={route['response_model']}")
    print(f"image_model_selection={route['image_model_selection']}")
    print(f"output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
