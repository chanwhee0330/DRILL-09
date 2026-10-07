"""Drill 9: move the boy with the arrow keys."""

from pathlib import Path

import pico2d

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 1024
RESOURCE_DIR = Path(__file__).resolve().parent


def main():
    pico2d.open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    try:
        tuk_ground = pico2d.load_image(str(RESOURCE_DIR / "TUK_GROUND.png"))
    finally:
        pico2d.close_canvas()


if __name__ == "__main__":
    main()
