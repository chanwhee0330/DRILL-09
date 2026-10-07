"""Tests for rendering order, exit handling, timing, and resource loading."""

from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

import Drill_09 as game


class GameLoopTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.ground = Mock()
        self.image = Mock(w=802, h=402)
        self.resources = self.stack.enter_context(
            patch.object(game, "load_resources", return_value=(self.ground, self.image))
        )
        self.api = {}
        for name in ("open_canvas", "close_canvas", "clear_canvas",
                     "update_canvas", "delay", "get_events"):
            self.api[name] = self.stack.enter_context(
                patch.object(game.pico2d, name)
            )
        self.api["get_events"].side_effect = [
            [], [SimpleNamespace(type=game.pico2d.SDL_QUIT, key=None)],
        ]
        self.clock = self.stack.enter_context(
            patch.object(game, "perf_counter", side_effect=[1, 1.02, 1.021, 1.04])
        )

    def test_background_is_drawn_before_boy_and_present(self):
        order = Mock()
        order.attach_mock(self.api["clear_canvas"], "clear")
        order.attach_mock(self.ground.draw, "background")
        order.attach_mock(self.image.clip_draw, "boy")
        order.attach_mock(self.api["update_canvas"], "present")
        game.main()
        self.assertEqual(order.mock_calls, [
            call.clear(),
            call.background(640, 512, 1280, 1024),
            call.boy(0, 300, 100, 100, 640, 512),
            call.present(),
        ])
        self.resources.assert_called_once_with()
        self.api["open_canvas"].assert_called_once_with(1280, 1024)
        self.api["close_canvas"].assert_called_once_with()

    def test_window_close_exits_before_update_or_draw(self):
        self.api["get_events"].side_effect = [
            [SimpleNamespace(type=game.pico2d.SDL_QUIT, key=None)],
        ]
        game.main()
        self.api["clear_canvas"].assert_not_called()
        self.image.clip_draw.assert_not_called()
        self.api["close_canvas"].assert_called_once_with()

    def test_escape_exits_before_rendering(self):
        self.api["get_events"].side_effect = [
            [SimpleNamespace(type=game.pico2d.SDL_KEYDOWN,
                             key=game.pico2d.SDLK_ESCAPE)],
        ]
        game.main()
        self.api["update_canvas"].assert_not_called()
        self.api["close_canvas"].assert_called_once_with()

    def test_load_error_still_closes_canvas(self):
        self.resources.side_effect = FileNotFoundError("missing test resource")
        with self.assertRaises(FileNotFoundError):
            game.main()
        self.api["close_canvas"].assert_called_once_with()

    def test_render_error_still_closes_canvas(self):
        self.ground.draw.side_effect = RuntimeError("test rendering error")
        with self.assertRaises(RuntimeError):
            game.main()
        self.api["close_canvas"].assert_called_once_with()

    def test_long_pause_passes_a_limited_delta_to_the_boy(self):
        self.clock.side_effect = [1, 9, 9.001, 9.02]
        with patch.object(game.Boy, "update", autospec=True) as update:
            game.main()
        self.assertEqual(update.call_count, 1)
        self.assertEqual(update.call_args.args[1], 0.1)

    def test_fast_frame_waits_only_for_the_remaining_budget(self):
        game.main()
        self.api["delay"].assert_called_once()
        wait = self.api["delay"].call_args.args[0]
        self.assertAlmostEqual(wait, 1 / 60 - 0.001)

    def test_slow_frame_does_not_add_a_delay(self):
        self.clock.side_effect = [1, 1.02, 1.08, 1.1]
        game.main()
        self.api["delay"].assert_not_called()

    def test_events_drive_movement_and_release_across_frames(self):
        self.api["get_events"].side_effect = [
            [SimpleNamespace(type=game.pico2d.SDL_KEYDOWN,
                             key=game.pico2d.SDLK_RIGHT)],
            [SimpleNamespace(type=game.pico2d.SDL_KEYUP,
                             key=game.pico2d.SDLK_RIGHT)],
            [SimpleNamespace(type=game.pico2d.SDL_QUIT, key=None)],
        ]
        self.clock.side_effect = [1, 1.02, 1.021, 1.04, 1.041, 1.06]
        game.main()
        draws = self.image.clip_draw.call_args_list
        self.assertEqual(len(draws), 2)
        self.assertEqual(draws[0].args[1], 100)
        self.assertEqual(draws[1].args[1], 300)
        self.assertAlmostEqual(draws[0].args[4], 644.8)
        self.assertAlmostEqual(draws[1].args[4], 644.8)


class ResourceTests(unittest.TestCase):
    def test_resources_load_using_absolute_script_paths(self):
        image = Mock(w=802, h=402)
        ground = Mock()
        with patch.object(game.pico2d, "load_image",
                          side_effect=[ground, image]) as loader:
            self.assertEqual(game.load_resources(), (ground, image))
        self.assertTrue(game.RESOURCE_DIR.is_absolute())
        self.assertEqual(loader.call_args_list, [
            call(str(game.RESOURCE_DIR / "TUK_GROUND.png")),
            call(str(game.RESOURCE_DIR / "animation_sheet.png")),
        ])

    def test_missing_resource_is_reported_before_texture_load(self):
        missing = game.RESOURCE_DIR / "__missing_drill_test_resources__"
        self.assertFalse(missing.exists())
        with patch.object(game, "RESOURCE_DIR", missing), \
                patch.object(game.pico2d, "load_image") as loader:
            with self.assertRaisesRegex(FileNotFoundError, "TUK_GROUND.png"):
                game.load_resources()
        loader.assert_not_called()

    def test_incomplete_sprite_sheet_is_rejected(self):
        for width, height in ((799, 402), (802, 399)):
            with self.subTest(size=(width, height)):
                with patch.object(game.pico2d, "load_image",
                                  side_effect=[Mock(), Mock(w=width, h=height)]):
                    with self.assertRaises(ValueError):
                        game.load_resources()


if __name__ == "__main__":
    unittest.main()
