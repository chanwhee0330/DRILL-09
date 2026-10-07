"""Regression tests for sprite animation and complete-sprite boundaries."""

import unittest
from unittest.mock import Mock

import Drill_09 as game


class AnimationBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.image = Mock()
        self.boy = game.Boy(self.image)

    def test_idle_animation_runs_without_position_change(self):
        position = self.boy.x, self.boy.y
        self.boy.update(0.125)
        self.assertEqual(self.boy.frame, 1)
        self.assertEqual(self.boy.state, game.IDLE)
        self.assertEqual((self.boy.x, self.boy.y), position)

    def test_idle_and_move_frames_loop_after_eight_frames(self):
        for moving in (False, True):
            with self.subTest(moving=moving):
                boy = game.Boy(Mock())
                if moving:
                    boy.pressed_keys.add(game.pico2d.SDLK_RIGHT)
                for tick in range(1, 19):
                    boy.update(0.125)
                    self.assertEqual(boy.frame, tick % 8)

    def test_state_changes_restart_animation(self):
        self.boy.update(0.5)
        self.assertEqual(self.boy.frame, 4)
        self.boy.pressed_keys.add(game.pico2d.SDLK_LEFT)
        self.boy.update(0)
        self.assertEqual(self.boy.state, game.MOVE)
        self.assertEqual(self.boy.frame, 0)
        self.boy.update(0.25)
        self.boy.pressed_keys.clear()
        self.boy.update(0)
        self.assertEqual(self.boy.state, game.IDLE)
        self.assertEqual(self.boy.frame, 0)
        self.assertEqual(self.boy.facing, game.LEFT)

    def test_unchanged_state_keeps_animation_time(self):
        self.boy.update(0.125)
        self.boy.update(0.125)
        self.assertEqual(self.boy.frame, 2)
        self.assertEqual(self.boy.animation_time, 0.25)

    def test_each_state_and_direction_uses_the_verified_row(self):
        cases = [
            (game.IDLE, game.RIGHT, 300),
            (game.IDLE, game.LEFT, 200),
            (game.MOVE, game.RIGHT, 100),
            (game.MOVE, game.LEFT, 0),
        ]
        for state, facing, bottom in cases:
            with self.subTest(state=state, facing=facing):
                self.boy.state, self.boy.facing = state, facing
                self.boy.frame = 7
                self.boy.draw()
                self.image.clip_draw.assert_called_with(
                    700, bottom, 100, 100, 640, 512,
                )

    def test_long_animation_time_keeps_frame_in_range(self):
        self.boy.update(1_000_000.125)
        self.assertEqual(self.boy.frame, 1)

    def test_all_four_edges_contain_the_complete_sprite(self):
        cases = [
            (game.pico2d.SDLK_LEFT, 50, 512),
            (game.pico2d.SDLK_RIGHT, 1230, 512),
            (game.pico2d.SDLK_DOWN, 640, 50),
            (game.pico2d.SDLK_UP, 640, 974),
        ]
        for key, x, y in cases:
            with self.subTest(key=key):
                boy = game.Boy(Mock())
                boy.pressed_keys.add(key)
                boy.update(100)
                self.assertEqual((boy.x, boy.y), (x, y))
                self.assertGreaterEqual(boy.x - 50, 0)
                self.assertLessEqual(boy.x + 50, 1280)
                self.assertGreaterEqual(boy.y - 50, 0)
                self.assertLessEqual(boy.y + 50, 1024)

    def test_all_four_corners_clamp_both_axes(self):
        for horizontal, x in ((game.pico2d.SDLK_LEFT, 50),
                              (game.pico2d.SDLK_RIGHT, 1230)):
            for vertical, y in ((game.pico2d.SDLK_DOWN, 50),
                                (game.pico2d.SDLK_UP, 974)):
                with self.subTest(keys=(horizontal, vertical)):
                    boy = game.Boy(Mock())
                    boy.pressed_keys.update((horizontal, vertical))
                    boy.update(100)
                    self.assertEqual((boy.x, boy.y), (x, y))

    def test_blocked_input_keeps_running_animation(self):
        self.boy.x = 50
        self.boy.pressed_keys.add(game.pico2d.SDLK_LEFT)
        self.boy.update(0.125)
        self.assertEqual(self.boy.x, 50)
        self.assertEqual(self.boy.state, game.MOVE)
        self.assertEqual(self.boy.frame, 1)
        self.boy.update(0.125)
        self.assertEqual(self.boy.frame, 2)

    def test_reversing_input_moves_away_from_an_edge(self):
        self.boy.x = 50
        self.boy.pressed_keys.add(game.pico2d.SDLK_RIGHT)
        self.boy.update(0.125)
        self.assertEqual(self.boy.x, 80)
        self.assertEqual(self.boy.facing, game.RIGHT)


if __name__ == "__main__":
    unittest.main()
