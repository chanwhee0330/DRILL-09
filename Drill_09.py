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
        running = True
        while running:
            for event in pico2d.get_events():
                if event.type == pico2d.SDL_QUIT:
                    running = False
            pico2d.clear_canvas()
            tuk_ground.draw(
                CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2,
                CANVAS_WIDTH, CANVAS_HEIGHT,
            )
            pico2d.update_canvas()
    finally:
        pico2d.close_canvas()


if __name__ == "__main__":
    main()
