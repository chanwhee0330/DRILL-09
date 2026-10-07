"""Drill 9: move the boy with the arrow keys."""

import pico2d


def main():
    pico2d.open_canvas()
    try:
        tuk_ground = pico2d.load_image("TUK_GROUND.png")
    finally:
        pico2d.close_canvas()


if __name__ == "__main__":
    main()
