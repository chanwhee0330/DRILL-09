"""Optional real SDL checks: DRILL_SDL_TEST=1 python -m unittest discover -s tests."""

import ctypes
import hashlib
import importlib
import os
from pathlib import Path
import struct
import unittest
from unittest.mock import patch
import zlib

import Drill_09 as game


def png_chunk(kind, payload):
    checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)


def save_preview(path, pixels):
    width, height = game.CANVAS_WIDTH, game.CANVAS_HEIGHT
    stride = width * 4
    scanlines = b"".join(
        b"\0" + pixels[y * stride:(y + 1) * stride] for y in range(height)
    )
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(scanlines))
        + png_chunk(b"IEND", b"")
    )


@unittest.skipUnless(os.environ.get("DRILL_SDL_TEST") == "1",
                     "Set DRILL_SDL_TEST=1 to run real SDL rendering checks")
class SDLRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        environment = patch.dict(os.environ, {
            "SDL_VIDEODRIVER": "dummy",
            "SDL_AUDIODRIVER": "dummy",
        })
        environment.start()
        cls.addClassCleanup(environment.stop)
        game.pico2d.open_canvas(game.CANVAS_WIDTH, game.CANVAS_HEIGHT)
        cls.addClassCleanup(game.pico2d.close_canvas)
        cls.canvas = importlib.import_module("pico2d.pico2d")
        # Dummy video has no accelerated renderer; use SDL's real software renderer.
        if not cls.canvas.renderer:
            cls.canvas.renderer = game.pico2d.SDL_CreateRenderer(
                cls.canvas.window, -1, game.pico2d.SDL_RENDERER_SOFTWARE,
            )
        if not cls.canvas.renderer:
            raise RuntimeError(game.pico2d.SDL_GetError().decode("utf-8"))
        cls.ground, cls.image = game.load_resources()

    def setUp(self):
        game.pico2d.get_events()

    def capture(self):
        pixels = ctypes.create_string_buffer(game.CANVAS_WIDTH * game.CANVAS_HEIGHT * 4)
        result = game.pico2d.SDL_RenderReadPixels(
            self.canvas.renderer, None, game.pico2d.SDL_PIXELFORMAT_RGBA32,
            pixels, game.CANVAS_WIDTH * 4,
        )
        self.assertEqual(result, 0, game.pico2d.SDL_GetError())
        return pixels.raw

    def render(self, boy=None):
        game.pico2d.clear_canvas()
        self.ground.draw(640, 512, 1280, 1024)
        if boy is not None:
            boy.draw()
        pixels = self.capture()
        game.pico2d.update_canvas()
        return pixels

    def push_key(self, event_type, key):
        event = game.pico2d.SDL_Event()
        event.type = event_type
        event.key.keysym.sym = key
        event.key.repeat = 0
        self.assertEqual(game.pico2d.SDL_PushEvent(ctypes.byref(event)), 1)

    def test_real_texture_dimensions(self):
        self.assertEqual((self.ground.w, self.ground.h), (1280, 1024))
        self.assertEqual((self.image.w, self.image.h), (802, 402))

    def test_real_key_events_reach_movement_and_release(self):
        boy = game.Boy(self.image)
        self.push_key(game.pico2d.SDL_KEYDOWN, game.pico2d.SDLK_LEFT)
        for event in game.pico2d.get_events():
            boy.handle_event(event)
        boy.update(0.125)
        self.assertEqual((boy.x, boy.y, boy.facing), (610, 512, game.LEFT))

        self.push_key(game.pico2d.SDL_KEYUP, game.pico2d.SDLK_LEFT)
        self.push_key(game.pico2d.SDL_KEYDOWN, game.pico2d.SDLK_UP)
        for event in game.pico2d.get_events():
            boy.handle_event(event)
        boy.update(0.125)
        self.assertEqual((boy.x, boy.y, boy.facing), (610, 542, game.LEFT))

        self.push_key(game.pico2d.SDL_KEYUP, game.pico2d.SDLK_UP)
        for event in game.pico2d.get_events():
            boy.handle_event(event)
        boy.update(0.125)
        self.assertEqual(boy.state, game.IDLE)

        quit_event = game.pico2d.SDL_Event()
        quit_event.type = game.pico2d.SDL_QUIT
        self.assertEqual(game.pico2d.SDL_PushEvent(ctypes.byref(quit_event)), 1)
        self.assertTrue(any(event.type == game.pico2d.SDL_QUIT
                            for event in game.pico2d.get_events()))

    def test_all_animation_rows_and_frames_render_over_the_background(self):
        background = self.render()
        boy = game.Boy(self.image)
        output = os.environ.get("DRILL_PREVIEW_DIR")
        if output:
            Path(output).mkdir(parents=True, exist_ok=True)
        for state in (game.IDLE, game.MOVE):
            for facing in (game.RIGHT, game.LEFT):
                hashes = set()
                for frame in range(8):
                    boy.state, boy.facing, boy.frame = state, facing, frame
                    pixels = self.render(boy)
                    self.assertNotEqual(pixels, background)
                    self.assertEqual(pixels[:1280 * 4], background[:1280 * 4])
                    hashes.add(hashlib.sha256(pixels).digest())
                    if frame == 0 and output:
                        save_preview(Path(output) / f"{state.lower()}_{facing.lower()}.png",
                                     pixels)
                self.assertGreater(len(hashes), 1)


if __name__ == "__main__":
    unittest.main()
