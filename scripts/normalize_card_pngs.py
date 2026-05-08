from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PNG_DIRS = [
    PROJECT_ROOT / "output" / "card_placeholders" / "heroes",
    PROJECT_ROOT / "output" / "card_placeholders" / "realm",
]
WHITE_THRESHOLD = 245


def is_background(pixel: tuple[int, int, int, int]) -> bool:
    r, g, b, a = pixel
    return a > 0 and r >= WHITE_THRESHOLD and g >= WHITE_THRESHOLD and b >= WHITE_THRESHOLD


def normalize_png(path: Path) -> bool:
    image = Image.open(path).convert("RGBA")
    pixels = image.load()
    width, height = image.size

    visited: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    changed = False
    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or not (0 <= x < width and 0 <= y < height):
            continue
        visited.add((x, y))

        if not is_background(pixels[x, y]):
            continue

        pixels[x, y] = (255, 255, 255, 0)
        changed = True
        queue.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))

    bbox = image.getchannel("A").getbbox()
    if bbox is not None and bbox != (0, 0, width, height):
        image = image.crop(bbox)
        changed = True

    if changed:
        image.save(path)
    return changed


def main() -> None:
    updated = 0
    for directory in PNG_DIRS:
        if not directory.is_dir():
            continue
        for path in directory.glob("*.png"):
            if normalize_png(path):
                updated += 1
    print(f"Normalized {updated} PNG card assets.")


if __name__ == "__main__":
    main()
