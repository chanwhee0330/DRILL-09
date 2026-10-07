"""Regression tests for arrow input and time-based movement."""

import math
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import Drill_09 as game


def send_key(boy, event_type, key):
    boy.handle_event(SimpleNamespace(type=event_type, key=key))


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.boy = game.Boy(Mock())

    def press(self, *keys):
        for key in keys:
            send_key(self.boy, game.pico2d.SDL_KEYDOWN, key)

    def release(self, *keys):
        for key in keys:
            send_key(self.boy, game.pico2d.SDL_KEYUP, key)

    def test_initial_position_and_state(self):
        self.assertEqual((self.boy.x, self.boy.y), (640, 512))
        self.assertEqual(self.boy.state, game.IDLE)
        self.assertEqual(self.boy.facing, game.RIGHT)

    def test_each_arrow_moves_in_its_expected_direction(self):
        cases = [
            (game.pico2d.SDLK_LEFT, -60, 0),
            (game.pico2d.SDLK_RIGHT, 60, 0),
            (game.pico2d.SDLK_UP, 0, 60),
            (game.pico2d.SDLK_DOWN, 0, -60),
        ]
        for key, dx, dy in cases:
            with self.subTest(key=key):
                boy = game.Boy(Mock())
                send_key(boy, game.pico2d.SDL_KEYDOWN, key)
                boy.update(0.25)
                self.assertAlmostEqual(boy.x, 640 + dx)
                self.assertAlmostEqual(boy.y, 512 + dy)
                self.assertEqual(boy.state, game.MOVE)

    def test_key_release_stops_movement(self):
        self.press(game.pico2d.SDLK_RIGHT)
        self.boy.update(0.25)
        self.release(game.pico2d.SDLK_RIGHT)
        stopped = self.boy.x, self.boy.y
        self.boy.update(0.25)
        self.assertEqual((self.boy.x, self.boy.y), stopped)
        self.assertEqual(self.boy.state, game.IDLE)

    def test_repeated_keydown_does_not_multiply_speed(self):
        self.press(*([game.pico2d.SDLK_LEFT] * 5))
        self.boy.update(0.25)
        self.assertEqual(self.boy.x, 580)
        self.release(game.pico2d.SDLK_LEFT)
        self.assertEqual(self.boy.pressed_keys, set())

    def test_unmatched_keyup_is_safe(self):
        self.release(game.pico2d.SDLK_UP)
        self.boy.update(0.25)
        self.assertEqual(self.boy.state, game.IDLE)

    def test_unrelated_keys_are_ignored(self):
        self.press(game.pico2d.SDLK_a)
        self.boy.update(0.25)
        self.assertEqual(self.boy.pressed_keys, set())
        self.assertEqual(self.boy.state, game.IDLE)

    def test_horizontal_opponents_cancel_and_resume(self):
        self.press(game.pico2d.SDLK_LEFT, game.pico2d.SDLK_RIGHT)
        self.boy.update(0.25)
        self.assertEqual(self.boy.x, 640)
        self.assertEqual(self.boy.state, game.IDLE)
        self.release(game.pico2d.SDLK_RIGHT)
        self.boy.update(0.25)
        self.assertEqual(self.boy.x, 580)
        self.assertEqual(self.boy.facing, game.LEFT)

    def test_vertical_opponents_cancel_and_resume(self):
        self.press(game.pico2d.SDLK_UP, game.pico2d.SDLK_DOWN)
        self.boy.update(0.25)
        self.assertEqual(self.boy.y, 512)
        self.release(game.pico2d.SDLK_DOWN)
        self.boy.update(0.25)
        self.assertEqual(self.boy.y, 572)

    def test_all_opponents_cancel(self):
        self.press(*game.ARROW_KEYS)
        self.boy.update(0.25)
        self.assertEqual((self.boy.x, self.boy.y), (640, 512))
        self.assertEqual(self.boy.state, game.IDLE)

    def test_vertical_movement_and_idle_preserve_left_facing(self):
        self.press(game.pico2d.SDLK_LEFT)
        self.boy.update(0.125)
        self.release(game.pico2d.SDLK_LEFT)
        for vertical in (game.pico2d.SDLK_UP, game.pico2d.SDLK_DOWN):
            self.press(vertical)
            self.boy.update(0.125)
            self.assertEqual(self.boy.facing, game.LEFT)
            self.release(vertical)
        self.boy.update(0.125)
        self.assertEqual(self.boy.state, game.IDLE)
        self.assertEqual(self.boy.facing, game.LEFT)

    def test_horizontal_input_changes_facing_during_vertical_movement(self):
        self.press(game.pico2d.SDLK_UP, game.pico2d.SDLK_LEFT)
        self.boy.update(0.125)
        self.release(game.pico2d.SDLK_LEFT)
        self.press(game.pico2d.SDLK_RIGHT)
        self.boy.update(0.125)
        self.assertEqual(self.boy.facing, game.RIGHT)

    def test_all_diagonals_have_cardinal_speed(self):
        for horizontal in (game.pico2d.SDLK_LEFT, game.pico2d.SDLK_RIGHT):
            for vertical in (game.pico2d.SDLK_UP, game.pico2d.SDLK_DOWN):
                with self.subTest(keys=(horizontal, vertical)):
                    boy = game.Boy(Mock())
                    boy.pressed_keys.update((horizontal, vertical))
                    boy.update(0.25)
                    self.assertAlmostEqual(math.hypot(boy.x - 640, boy.y - 512), 60)

    def test_movement_is_independent_of_update_frequency(self):
        single = game.Boy(Mock())
        divided = game.Boy(Mock())
        single.pressed_keys.add(game.pico2d.SDLK_RIGHT)
        divided.pressed_keys.add(game.pico2d.SDLK_RIGHT)
        single.update(0.25)
        for _ in range(10):
            divided.update(0.025)
        self.assertAlmostEqual(single.x, divided.x)

    def test_zero_time_does_not_move(self):
        self.press(game.pico2d.SDLK_LEFT)
        self.boy.update(0)
        self.assertEqual((self.boy.x, self.boy.y), (640, 512))


if __name__ == "__main__":
    unittest.main()
