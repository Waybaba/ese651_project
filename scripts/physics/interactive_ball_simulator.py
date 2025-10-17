#!/usr/bin/env python3
"""
Interactive Ball Simulator
A physics-based game where you control a ball with keyboard forces to score.
"""

import pygame
import numpy as np
import sys
from typing import Tuple
import math

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60

# Colors (RGB)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# Physics constants
GRAVITY = -9.81  # m/s^2
FRICTION_COEFF = 0.1  # Reduced friction for easier movement
BALL_MASS = 1.0  # kg
BALL_RADIUS = 0.1  # m
FORCE_MAGNITUDE = 200.0  # Increased force for more responsive movement

# Game constants
GROUND_Y = 50  # pixels from bottom
GOAL_X = 800  # pixels from left
GOAL_Y_MIN = 200  # pixels from top
GOAL_Y_MAX = 400  # pixels from top
MIN_DISTANCE_FROM_GOAL = 1.0  # meters

# Scale factor: pixels per meter
PIXELS_PER_METER = 100


class PhysicsEngine:
    """Simple 2D physics engine for the ball simulation."""

    def __init__(self):
        self.dt = 1.0 / FPS  # time step

    def update_ball(self, ball_pos: np.ndarray, ball_vel: np.ndarray,
                    applied_force: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Update ball physics using semi-implicit Euler integration.

        Args:
            ball_pos: Current position [x, y] in meters
            ball_vel: Current velocity [vx, vy] in m/s
            applied_force: Applied force [fx, fy] in Newtons

        Returns:
            Updated position and velocity
        """
        # Convert to numpy arrays for easier computation
        pos = np.array(ball_pos, dtype=float)  # shape: (2,)
        vel = np.array(ball_vel, dtype=float)  # shape: (2,)
        force = np.array(applied_force, dtype=float)  # shape: (2,)

        # Gravity force
        gravity_force = np.array([0, GRAVITY * BALL_MASS])  # shape: (2,)

        # Check for ground contact
        ground_y_meters = GROUND_Y / PIXELS_PER_METER
        if pos[1] <= ground_y_meters + BALL_RADIUS:
            # Normal force to prevent penetration
            normal_force = np.array([0, -GRAVITY * BALL_MASS])  # shape: (2,)

            # Friction force (Coulomb friction with smooth approximation)
            if abs(vel[0]) > 0.01:  # Avoid division by zero
                friction_magnitude = FRICTION_COEFF * abs(normal_force[1])
                friction_force = np.array([
                    -friction_magnitude * np.sign(vel[0]), 0
                ])  # shape: (2,)
            else:
                friction_force = np.array([0, 0])  # shape: (2,)

            # Total force when in contact
            total_force = (force + gravity_force + normal_force +
                          friction_force)  # shape: (2,)

            # Constrain position to ground
            pos[1] = ground_y_meters + BALL_RADIUS
            if vel[1] < 0:  # Only stop downward velocity
                vel[1] = 0
        else:
            # Free fall
            total_force = force + gravity_force  # shape: (2,)

        # Calculate acceleration
        acceleration = total_force / BALL_MASS  # shape: (2,)

        # Semi-implicit Euler integration
        vel = vel + acceleration * self.dt  # shape: (2,)
        pos = pos + vel * self.dt  # shape: (2,)

        return pos, vel


class Ball:
    """Ball object with physics properties."""

    def __init__(self, x: float, y: float):
        self.pos = np.array([x, y], dtype=float)  # position in meters, shape: (2,)
        self.vel = np.array([0, 0], dtype=float)  # velocity in m/s, shape: (2,)
        self.radius = BALL_RADIUS
        self.trajectory = []  # List of positions for trajectory display

    def update(self, physics_engine: PhysicsEngine, applied_force: np.ndarray):
        """Update ball physics and trajectory."""
        self.pos, self.vel = physics_engine.update_ball(
            self.pos, self.vel, applied_force)

        # Add to trajectory (limit length for performance)
        self.trajectory.append(self.pos.copy())
        if len(self.trajectory) > 200:  # Keep last 200 points
            self.trajectory.pop(0)

    def get_screen_pos(self) -> Tuple[int, int]:
        """Convert physics position to screen coordinates."""
        screen_x = int(self.pos[0] * PIXELS_PER_METER)
        screen_y = (SCREEN_HEIGHT - int(self.pos[1] * PIXELS_PER_METER) -
                   GROUND_Y)
        return screen_x, screen_y

    def reset(self, x: float, y: float):
        """Reset ball to initial position."""
        self.pos = np.array([x, y], dtype=float)
        self.vel = np.array([0, 0], dtype=float)
        self.trajectory = []


class Goal:
    """Goal line segment for scoring."""

    def __init__(self, x: float, y_min: float, y_max: float):
        self.x = x  # x position in meters
        self.y_min = y_min  # y position in meters
        self.y_max = y_max  # y position in meters

    def get_screen_coords(self) -> Tuple[int, int, int, int]:
        """Convert goal coordinates to screen coordinates."""
        screen_x = int(self.x * PIXELS_PER_METER)
        screen_y_min = (SCREEN_HEIGHT - int(self.y_min * PIXELS_PER_METER) -
                       GROUND_Y)
        screen_y_max = (SCREEN_HEIGHT - int(self.y_max * PIXELS_PER_METER) -
                       GROUND_Y)
        return screen_x, screen_y_min, screen_x, screen_y_max

    def check_goal(self, ball_pos: np.ndarray,
                   ball_prev_pos: np.ndarray) -> bool:
        """
        Check if ball crossed the goal line.

        Args:
            ball_pos: Current ball position [x, y] in meters, shape: (2,)
            ball_prev_pos: Previous ball position [x, y] in meters, shape: (2,)

        Returns:
            True if goal was scored
        """
        # Check if ball crossed the goal line
        if ((ball_prev_pos[0] < self.x and ball_pos[0] >= self.x) or
                (ball_prev_pos[0] > self.x and ball_pos[0] <= self.x)):
            # Check if y coordinate is within goal range
            if self.y_min <= ball_pos[1] <= self.y_max:
                return True
        return False


class Game:
    """Main game class managing the simulation."""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Interactive Ball Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Initialize physics and objects
        self.physics_engine = PhysicsEngine()

        # Convert screen coordinates to meters for initial position
        initial_x = 2.0  # 2 meters from left
        initial_y = GROUND_Y / PIXELS_PER_METER + BALL_RADIUS  # On ground

        self.ball = Ball(initial_x, initial_y)
        self.goal = Goal(
            GOAL_X / PIXELS_PER_METER,
            (SCREEN_HEIGHT - GOAL_Y_MAX - GROUND_Y) / PIXELS_PER_METER,
            (SCREEN_HEIGHT - GOAL_Y_MIN - GROUND_Y) / PIXELS_PER_METER)

        # Game state
        self.score = 0
        self.game_state = "playing"  # "playing", "scored", "reset"
        self.applied_force = np.array([0, 0], dtype=float)  # shape: (2,)

    def handle_events(self):
        """Handle keyboard and mouse events."""
        self.applied_force = np.array([0, 0], dtype=float)  # Reset force each frame

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                # Print key press events
                key_name = pygame.key.name(event.key)
                print(f"Key pressed: {key_name}")
                
                if event.key == pygame.K_r:
                    print("Resetting game...")
                    self.reset_game()
                elif event.key == pygame.K_ESCAPE:
                    print("Exiting game...")
                    return False

        # Handle continuous key presses
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:  # Up
            self.applied_force[1] += FORCE_MAGNITUDE
            print("W key held - applying upward force")
        if keys[pygame.K_s]:  # Down
            self.applied_force[1] -= FORCE_MAGNITUDE
            print("S key held - applying downward force")
        if keys[pygame.K_a]:  # Left
            self.applied_force[0] -= FORCE_MAGNITUDE
            print("A key held - applying leftward force")
        if keys[pygame.K_d]:  # Right
            self.applied_force[0] += FORCE_MAGNITUDE
            print("D key held - applying rightward force")

        return True
    
    def update(self):
        """Update game state."""
        if self.game_state == "playing":
            # Store previous position for goal detection
            prev_pos = self.ball.pos.copy()

            # Update ball physics
            self.ball.update(self.physics_engine, self.applied_force)

        # Check for goal
            if self.goal.check_goal(self.ball.pos, prev_pos):
            self.score += 1
                self.game_state = "scored"

    def draw(self):
        """Draw all game elements."""
        self.screen.fill(WHITE)

        # Draw ground
        pygame.draw.line(self.screen, BLACK, (0, SCREEN_HEIGHT - GROUND_Y),
                        (SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y), 3)

        # Draw goal
        goal_x1, goal_y1, goal_x2, goal_y2 = self.goal.get_screen_coords()
        pygame.draw.line(self.screen, RED, (goal_x1, goal_y1),
                        (goal_x2, goal_y2), 5)

        # Draw goal posts
        pygame.draw.circle(self.screen, RED, (goal_x1, goal_y1), 8)
        pygame.draw.circle(self.screen, RED, (goal_x2, goal_y2), 8)

        # Draw ball trajectory
        if len(self.ball.trajectory) > 1:
            screen_trajectory = []
            for pos in self.ball.trajectory:
                screen_x = int(pos[0] * PIXELS_PER_METER)
                screen_y = (SCREEN_HEIGHT - int(pos[1] * PIXELS_PER_METER) -
                           GROUND_Y)
                screen_trajectory.append((screen_x, screen_y))
            pygame.draw.lines(self.screen, BLUE, False, screen_trajectory, 2)

        # Draw ball
        ball_screen_x, ball_screen_y = self.ball.get_screen_pos()
        pygame.draw.circle(self.screen, YELLOW, (ball_screen_x, ball_screen_y),
                          int(BALL_RADIUS * PIXELS_PER_METER))
        pygame.draw.circle(self.screen, BLACK, (ball_screen_x, ball_screen_y),
                          int(BALL_RADIUS * PIXELS_PER_METER), 2)

        # Draw force vector
        if np.linalg.norm(self.applied_force) > 0.1:
            force_scale = 0.5  # Scale for visualization
            force_end_x = ball_screen_x + int(self.applied_force[0] * force_scale)
            force_end_y = ball_screen_y - int(self.applied_force[1] * force_scale)
            pygame.draw.line(self.screen, ORANGE, (ball_screen_x, ball_screen_y),
                           (force_end_x, force_end_y), 3)
            # Draw arrowhead
            arrow_length = 10
            angle = math.atan2(force_end_y - ball_screen_y,
                              force_end_x - ball_screen_x)
            arrow_x1 = force_end_x - arrow_length * math.cos(angle - math.pi/6)
            arrow_y1 = force_end_y - arrow_length * math.sin(angle - math.pi/6)
            arrow_x2 = force_end_x - arrow_length * math.cos(angle + math.pi/6)
            arrow_y2 = force_end_y - arrow_length * math.sin(angle + math.pi/6)
            pygame.draw.line(self.screen, ORANGE, (force_end_x, force_end_y),
                           (arrow_x1, arrow_y1), 3)
            pygame.draw.line(self.screen, ORANGE, (force_end_x, force_end_y),
                           (arrow_x2, arrow_y2), 3)

        # Draw UI
        self.draw_ui()

        pygame.display.flip()
    
    def draw_ui(self):
        """Draw user interface elements."""
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        self.screen.blit(score_text, (10, 10))

        # Instructions
        instructions = [
            "WASD: Apply forces to ball",
            "R: Reset game",
            "ESC: Quit"
        ]
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, BLACK)
            self.screen.blit(text, (10, 50 + i * 25))

        # Game state
        if self.game_state == "scored":
            goal_text = self.font.render("GOAL!", True, GREEN)
            text_rect = goal_text.get_rect(center=(SCREEN_WIDTH//2, 100))
            self.screen.blit(goal_text, text_rect)

        # Ball position and velocity info
        pos_text = self.small_font.render(
            f"Position: ({self.ball.pos[0]:.2f}, {self.ball.pos[1]:.2f}) m",
            True, BLACK)
        vel_text = self.small_font.render(
            f"Velocity: ({self.ball.vel[0]:.2f}, {self.ball.vel[1]:.2f}) m/s",
            True, BLACK)
        self.screen.blit(pos_text, (10, SCREEN_HEIGHT - 60))
        self.screen.blit(vel_text, (10, SCREEN_HEIGHT - 35))

    def reset_game(self):
        """Reset the game to initial state."""
        initial_x = 2.0  # 2 meters from left
        initial_y = GROUND_Y / PIXELS_PER_METER + BALL_RADIUS  # On ground
        self.ball.reset(initial_x, initial_y)
        self.game_state = "playing"

    def run(self):
        """Main game loop."""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


def main():
    """Main function to start the game."""
    print("Starting Interactive Ball Simulator...")
    print("Controls:")
    print("  W - Apply upward force")
    print("  S - Apply downward force")
    print("  A - Apply leftward force")
    print("  D - Apply rightward force")
    print("  R - Reset game")
    print("  ESC - Quit")
    print("\nGoal: Get the ball through the red goal line!")

    game = Game()
    game.run()


if __name__ == "__main__":
    main()
