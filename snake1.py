"""Simple Snake game for Pyxel Web."""

# title: Snake
# author: Codex
# desc: A browser-playable snake game built with Pyxel
# license: MIT

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import random

import pyxel


CELL_SIZE = 8
GRID_WIDTH = 20
GRID_HEIGHT = 15
HEADER_HEIGHT = 16
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
SCREEN_HEIGHT = HEADER_HEIGHT + GRID_HEIGHT * CELL_SIZE

DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)


@dataclass(frozen=True)
class Point:
    x: int
    y: int


class SnakeGame:
    def __init__(self) -> None:
        pyxel.init(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            title="Snake",
            fps=30,
            quit_key=pyxel.KEY_NONE,
        )
        self.best_score = 0
        self.state = "title"
        self.blink = True
        self.random = random.Random()
        self.reset()
        pyxel.run(self.update, self.draw)

    def reset(self) -> None:
        start_x = GRID_WIDTH // 2
        start_y = GRID_HEIGHT // 2
        self.snake = deque(
            [
                Point(start_x, start_y),
                Point(start_x - 1, start_y),
                Point(start_x - 2, start_y),
            ]
        )
        self.direction = DIR_RIGHT
        self.pending_direction = DIR_RIGHT
        self.food = self.spawn_food()
        self.score = 0
        self.steps = 0
        self.move_timer = 0
        self.flash_timer = 0

    def spawn_food(self) -> Point:
        occupied = set(self.snake)
        choices = [
            Point(x, y)
            for y in range(GRID_HEIGHT)
            for x in range(GRID_WIDTH)
            if Point(x, y) not in occupied
        ]
        return self.random.choice(choices)

    def update(self) -> None:
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()

        if pyxel.frame_count % 20 == 0:
            self.blink = not self.blink

        if self.state == "title":
            self.update_title()
        elif self.state == "playing":
            self.update_playing()
        else:
            self.update_game_over()

    def update_title(self) -> None:
        if self.start_pressed():
            self.reset()
            self.state = "playing"

    def update_game_over(self) -> None:
        if self.flash_timer > 0:
            self.flash_timer -= 1
        if self.start_pressed():
            self.reset()
            self.state = "playing"

    def update_playing(self) -> None:
        next_direction = self.read_direction()
        if next_direction is not None and not self.is_reverse(next_direction):
            self.pending_direction = next_direction

        self.move_timer += 1
        if self.move_timer < self.move_interval:
            return

        self.move_timer = 0
        self.direction = self.pending_direction
        head = self.snake[0]
        new_head = Point(head.x + self.direction[0], head.y + self.direction[1])
        grow = new_head == self.food
        body_to_check = self.snake if grow else list(self.snake)[:-1]

        if self.hit_wall(new_head) or new_head in body_to_check:
            self.best_score = max(self.best_score, self.score)
            self.state = "game_over"
            self.flash_timer = 18
            return

        self.snake.appendleft(new_head)
        if grow:
            self.score += 1
            self.steps += 1
            self.food = self.spawn_food()
        else:
            self.snake.pop()

    @property
    def move_interval(self) -> int:
        return max(3, 7 - self.score // 4)

    def read_direction(self) -> tuple[int, int] | None:
        if pyxel.btnp(pyxel.KEY_UP) or pyxel.btnp(pyxel.KEY_W):
            return DIR_UP
        if pyxel.btnp(pyxel.KEY_DOWN) or pyxel.btnp(pyxel.KEY_S):
            return DIR_DOWN
        if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_A):
            return DIR_LEFT
        if pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_D):
            return DIR_RIGHT
        return None

    def start_pressed(self) -> bool:
        return (
            pyxel.btnp(pyxel.KEY_SPACE)
            or pyxel.btnp(pyxel.KEY_RETURN)
            or pyxel.btnp(pyxel.KEY_KP_ENTER)
        )

    def is_reverse(self, direction: tuple[int, int]) -> bool:
        return (
            len(self.snake) > 1
            and direction[0] == -self.direction[0]
            and direction[1] == -self.direction[1]
        )

    def hit_wall(self, point: Point) -> bool:
        return not (0 <= point.x < GRID_WIDTH and 0 <= point.y < GRID_HEIGHT)

    def draw(self) -> None:
        pyxel.cls(0)
        self.draw_header()
        self.draw_board()

        if self.state == "title":
            self.draw_title()
        elif self.state == "game_over":
            self.draw_game_over()

    def draw_header(self) -> None:
        pyxel.rect(0, 0, SCREEN_WIDTH, HEADER_HEIGHT, 1)
        pyxel.text(6, 5, f"SCORE {self.score:02}", 7)
        pyxel.text(92, 5, f"BEST {self.best_score:02}", 10)

    def draw_board(self) -> None:
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                color = 3 if (x + y) % 2 == 0 else 11
                self.draw_cell(Point(x, y), color)

        self.draw_food()
        self.draw_snake()

        pyxel.rectb(0, HEADER_HEIGHT, SCREEN_WIDTH, GRID_HEIGHT * CELL_SIZE, 7)

    def draw_food(self) -> None:
        x, y = self.to_screen(self.food)
        pyxel.rect(x + 1, y + 1, CELL_SIZE - 2, CELL_SIZE - 2, 8)
        pyxel.pset(x + 2, y + 2, 7)

    def draw_snake(self) -> None:
        for index, segment in enumerate(self.snake):
            x, y = self.to_screen(segment)
            color = 9 if index == 0 else 10
            pyxel.rect(x + 1, y + 1, CELL_SIZE - 2, CELL_SIZE - 2, color)

            if index == 0:
                eye_y = y + 2
                if self.direction == DIR_UP:
                    pyxel.pset(x + 2, y + 2, 7)
                    pyxel.pset(x + 5, y + 2, 7)
                elif self.direction == DIR_DOWN:
                    pyxel.pset(x + 2, y + 5, 7)
                    pyxel.pset(x + 5, y + 5, 7)
                elif self.direction == DIR_LEFT:
                    pyxel.pset(x + 2, eye_y, 7)
                    pyxel.pset(x + 2, y + 5, 7)
                else:
                    pyxel.pset(x + 5, eye_y, 7)
                    pyxel.pset(x + 5, y + 5, 7)

    def draw_title(self) -> None:
        pyxel.rect(18, 30, 124, 60, 0)
        pyxel.rectb(18, 30, 124, 60, 7)
        pyxel.text(60, 40, "SNAKE", 8)
        pyxel.text(34, 56, "ARROWS / WASD TO MOVE", 7)
        pyxel.text(41, 66, "EAT FOOD, AVOID WALLS", 6)
        if self.blink:
            pyxel.text(43, 80, "PRESS SPACE TO START", 10)

    def draw_game_over(self) -> None:
        if self.flash_timer % 4 < 2:
            pyxel.rect(26, 44, 108, 34, 0)
            pyxel.rectb(26, 44, 108, 34, 8)
            pyxel.text(53, 52, "GAME OVER", 8)
            pyxel.text(50, 62, f"SCORE {self.score:02}", 7)
            if self.blink:
                pyxel.text(35, 70, "PRESS SPACE TO RETRY", 10)

    def draw_cell(self, point: Point, color: int) -> None:
        x, y = self.to_screen(point)
        pyxel.rect(x, y, CELL_SIZE, CELL_SIZE, color)

    def to_screen(self, point: Point) -> tuple[int, int]:
        return point.x * CELL_SIZE, HEADER_HEIGHT + point.y * CELL_SIZE


SnakeGame()
