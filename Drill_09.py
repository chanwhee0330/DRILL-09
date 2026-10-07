"""Drill 9: move the boy with the arrow keys."""

from pathlib import Path

import pico2d

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 1024
RESOURCE_DIR = Path(__file__).resolve().parent
FRAME_WIDTH = 100
FRAME_HEIGHT = 100
FRAME_COUNT = 8
ARROW_KEYS = {
    pico2d.SDLK_LEFT, pico2d.SDLK_RIGHT,
    pico2d.SDLK_UP, pico2d.SDLK_DOWN,
}


class Boy:
    def __init__(self, image):
        self.image = image
        self.x = CANVAS_WIDTH / 2
        self.y = CANVAS_HEIGHT / 2
        self.frame = 0
        self.pressed_keys = set()

    def draw(self):
        self.image.clip_draw(
            self.frame * FRAME_WIDTH, 3 * FRAME_HEIGHT,
            FRAME_WIDTH, FRAME_HEIGHT, self.x, self.y,
        )


def main():
    pico2d.open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    try:
        tuk_ground = pico2d.load_image(str(RESOURCE_DIR / "TUK_GROUND.png"))
        character = pico2d.load_image(str(RESOURCE_DIR / "animation_sheet.png"))
        boy = Boy(character)
        running = True
        while running:
            for event in pico2d.get_events():
                if event.type == pico2d.SDL_QUIT:
                    running = False
                elif event.type == pico2d.SDL_KEYDOWN:
                    if event.key == pico2d.SDLK_ESCAPE:
                        running = False
            pico2d.clear_canvas()
            tuk_ground.draw(
                CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2,
                CANVAS_WIDTH, CANVAS_HEIGHT,
            )
            boy.draw()
            pico2d.update_canvas()
    finally:
        pico2d.close_canvas()


if __name__ == "__main__":
    main()
