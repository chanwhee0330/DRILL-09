"""Drill 9: move the boy with the arrow keys."""

from pathlib import Path

import pico2d

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 1024
RESOURCE_DIR = Path(__file__).resolve().parent
FRAME_WIDTH = 100
FRAME_HEIGHT = 100
FRAME_COUNT = 8
MOVE_SPEED = 4.0
ANIMATION_FPS = 8.0
LEFT = "LEFT"
RIGHT = "RIGHT"
IDLE = "IDLE"
MOVE = "MOVE"
# Rows are numbered from the bottom, as required by pico2d.clip_draw.
ANIMATION_ROWS = {
    (IDLE, RIGHT): 3,
    (IDLE, LEFT): 2,
    (MOVE, RIGHT): 1,
    (MOVE, LEFT): 0,
}
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
        self.animation_time = 0.0
        self.pressed_keys = set()
        self.dir_x = 0
        self.dir_y = 0
        self.speed = MOVE_SPEED
        self.facing = RIGHT
        self.state = IDLE

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN and event.key in ARROW_KEYS:
            self.pressed_keys.add(event.key)
        elif event.type == pico2d.SDL_KEYUP and event.key in ARROW_KEYS:
            self.pressed_keys.discard(event.key)

    def update(self):
        self.dir_x = (
            int(pico2d.SDLK_RIGHT in self.pressed_keys)
            - int(pico2d.SDLK_LEFT in self.pressed_keys)
        )
        self.dir_y = (
            int(pico2d.SDLK_UP in self.pressed_keys)
            - int(pico2d.SDLK_DOWN in self.pressed_keys)
        )
        next_state = MOVE if self.dir_x or self.dir_y else IDLE
        if next_state != self.state:
            self.animation_time = 0.0
        self.state = next_state
        if self.dir_x < 0:
            self.facing = LEFT
        elif self.dir_x > 0:
            self.facing = RIGHT
        self.x += self.dir_x * self.speed
        self.y += self.dir_y * self.speed
        self.animation_time += 1 / 60
        self.frame = int(self.animation_time * ANIMATION_FPS) % FRAME_COUNT

    def draw(self):
        row = ANIMATION_ROWS[(self.state, self.facing)]
        self.image.clip_draw(
            self.frame * FRAME_WIDTH, row * FRAME_HEIGHT,
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
                boy.handle_event(event)
            boy.update()
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
