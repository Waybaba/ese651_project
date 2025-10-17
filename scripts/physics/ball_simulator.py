#!/usr/bin/env python3
"""
Interactive Ball Simulator
A physics-based game where you control a ball with keyboard forces to score.
"""

import pygame
import numpy as np
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# Physics constants
GRAVITY = -9.81  # m/s^2
FRICTION_COEFF = 0.1  # Reduced friction for easier movement
BALL_MASS = 1.0  # kg
BALL_RADIUS = 0.1  # m
FORCE_MAGNITUDE = 80.0  # Increased force for more responsive movement
MOMENT_OF_INERTIA = 0.5 * BALL_MASS * BALL_RADIUS * BALL_RADIUS  # Solid sphere
RESTITUTION = 0.7  # Coefficient of restitution (bounciness)

# Game constants
GROUND_Y = 50  # pixels from bottom
GOAL_X = 800  # pixels from left
GOAL_Y_MIN = 200  # pixels from top
GOAL_Y_MAX = 400  # pixels from top

# Scale factor: pixels per meter
PIXELS_PER_METER = 100


class PhysicsEngine:
    """Simple 2D physics engine for the ball simulation."""

    def __init__(self):
        self.dt = 1.0 / FPS

    def update_ball(self, ball_pos, ball_vel, ball_angular_vel, applied_force):
        """Update ball physics using semi-implicit Euler integration."""
        pos = np.array(ball_pos, dtype=float)
        vel = np.array(ball_vel, dtype=float)
        angular_vel = float(ball_angular_vel)
        force = np.array(applied_force, dtype=float)


        # Gravity force
        gravity_force = np.array([0, GRAVITY * BALL_MASS])

        # Check for ground contact
        ground_y_meters = GROUND_Y / PIXELS_PER_METER
        torque = 0.0  # Initialize torque
        
        if pos[1] <= ground_y_meters + BALL_RADIUS:
            # Normal force to prevent penetration
            normal_force = np.array([0, -GRAVITY * BALL_MASS])

            # Handle bouncing first
            if vel[1] < 0:  # Ball is moving downward
                # Bounce with energy loss
                vel[1] = -vel[1] * RESTITUTION

            # Rolling vs sliding condition
            # For rolling without slipping: v = ω * r
            # In our coordinate system: v_x = -ω * r (negative because positive ω is counter-clockwise)
            expected_angular_vel = -vel[0] / BALL_RADIUS
            
            # Check if ball is rolling or sliding
            angular_vel_diff = abs(angular_vel - expected_angular_vel)
            is_rolling = angular_vel_diff < 0.1 and abs(vel[0]) > 0.01
            
            if is_rolling:
                # Ball is rolling without slipping
                # Rolling friction is much smaller than sliding friction
                rolling_friction_coeff = FRICTION_COEFF * 0.1  # Much smaller friction
                friction_magnitude = rolling_friction_coeff * abs(normal_force[1])
                friction_force = np.array([
                    -friction_magnitude * np.sign(vel[0]), 0
                ])
                # Small rolling resistance torque
                torque = -friction_force[0] * BALL_RADIUS
            else:
                # Ball is sliding or stationary
                if abs(vel[0]) > 0.01:
                    # Kinetic friction (sliding)
                    friction_magnitude = FRICTION_COEFF * abs(normal_force[1])
                    friction_force = np.array([
                        -friction_magnitude * np.sign(vel[0]), 0
                    ])
                    # Torque from friction that tries to make ball roll
                    # If ball slides right (vel[0] > 0), friction creates counter-clockwise torque
                    torque = friction_force[0] * BALL_RADIUS
                else:
                    # Static friction - check if applied force exceeds static friction limit
                    static_friction_limit = FRICTION_COEFF * abs(normal_force[1])
                    if abs(force[0]) <= static_friction_limit:
                        # Static friction prevents motion
                        friction_force = -force  # Friction exactly opposes applied force
                        torque = 0.0
                    else:
                        # Applied force exceeds static friction - ball starts sliding
                        friction_magnitude = FRICTION_COEFF * abs(normal_force[1])
                        friction_force = np.array([
                            -friction_magnitude * np.sign(force[0]), 0
                        ])
                        torque = friction_force[0] * BALL_RADIUS

            # Total force when in contact
            total_force = (force + gravity_force + normal_force +
                           friction_force)

            # Constrain position to ground
            pos[1] = ground_y_meters + BALL_RADIUS
        else:
            # Free fall
            total_force = force + gravity_force

        # Calculate acceleration and angular acceleration
        acceleration = total_force / BALL_MASS
        angular_acceleration = torque / MOMENT_OF_INERTIA

        # Semi-implicit Euler integration
        vel = vel + acceleration * self.dt
        pos = pos + vel * self.dt
        angular_vel = angular_vel + angular_acceleration * self.dt

        return pos, vel, angular_vel


class Ball:
    """Ball object with physics properties."""

    def __init__(self, x, y):
        self.pos = np.array([x, y], dtype=float)
        self.vel = np.array([0, 0], dtype=float)
        self.angular_vel = 0.0  # rad/s
        self.rotation = 0.0  # rad, current rotation angle
        self.radius = BALL_RADIUS
        self.trajectory = []

    def update(self, physics_engine, applied_force):
        """Update ball physics and trajectory."""
        old_pos = self.pos.copy()
        old_vel = self.vel.copy()
        
        self.pos, self.vel, self.angular_vel = physics_engine.update_ball(
            self.pos, self.vel, self.angular_vel, applied_force)
        
        # Update rotation angle
        self.rotation += self.angular_vel * physics_engine.dt


        # Add to trajectory
        self.trajectory.append(self.pos.copy())
        if len(self.trajectory) > 200:
            self.trajectory.pop(0)

    def get_screen_pos(self):
        """Convert physics position to screen coordinates."""
        screen_x = int(self.pos[0] * PIXELS_PER_METER)
        screen_y = (SCREEN_HEIGHT - int(self.pos[1] * PIXELS_PER_METER) -
                   GROUND_Y)
        return screen_x, screen_y

    def reset(self, x, y):
        """Reset ball to initial position."""
        self.pos = np.array([x, y], dtype=float)
        self.vel = np.array([0, 0], dtype=float)
        self.angular_vel = 0.0
        self.rotation = 0.0
        self.trajectory = []


class Goal:
    """Goal line segment for scoring."""

    def __init__(self, x, y_min, y_max):
        self.x = x
        self.y_min = y_min
        self.y_max = y_max

    def get_screen_coords(self):
        """Convert goal coordinates to screen coordinates."""
        screen_x = int(self.x * PIXELS_PER_METER)
        screen_y_min = (SCREEN_HEIGHT - int(self.y_min * PIXELS_PER_METER) -
                       GROUND_Y)
        screen_y_max = (SCREEN_HEIGHT - int(self.y_max * PIXELS_PER_METER) -
                       GROUND_Y)
        return screen_x, screen_y_min, screen_x, screen_y_max

    def check_goal(self, ball_pos, ball_prev_pos):
        """Check if ball crossed the goal line."""
        if ((ball_prev_pos[0] < self.x and ball_pos[0] >= self.x) or
                (ball_prev_pos[0] > self.x and ball_pos[0] <= self.x)):
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

        self.physics_engine = PhysicsEngine()

        initial_x = 2.0
        initial_y = GROUND_Y / PIXELS_PER_METER + BALL_RADIUS  # On ground

        self.ball = Ball(initial_x, initial_y)
        self.goal = Goal(
            GOAL_X / PIXELS_PER_METER,
            (SCREEN_HEIGHT - GOAL_Y_MAX - GROUND_Y) / PIXELS_PER_METER,
            (SCREEN_HEIGHT - GOAL_Y_MIN - GROUND_Y) / PIXELS_PER_METER)

        self.score = 0
        self.game_state = "playing"
        self.applied_force = np.array([0, 0], dtype=float)
        
        # Force impulse system
        self.force_impulses = []  # List of (force_vector, remaining_frames)
        self.impulse_duration = 3  # Number of frames to apply force (shorter duration)

    def handle_events(self):
        """Handle keyboard and mouse events."""
        # Calculate total force from all active impulses
        self.applied_force = np.array([0, 0], dtype=float)
        for force_vector, _ in self.force_impulses:
            self.applied_force += force_vector

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_r:
                    self.reset_game()
                elif event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_w:
                    # Add upward force impulse
                    impulse_force = np.array([0, FORCE_MAGNITUDE])
                    self.force_impulses.append((impulse_force, self.impulse_duration))
                elif event.key == pygame.K_s:
                    # Add downward force impulse
                    impulse_force = np.array([0, -FORCE_MAGNITUDE])
                    self.force_impulses.append((impulse_force, self.impulse_duration))
                elif event.key == pygame.K_a:
                    # Add leftward force impulse
                    impulse_force = np.array([-FORCE_MAGNITUDE, 0])
                    self.force_impulses.append((impulse_force, self.impulse_duration))
                elif event.key == pygame.K_d:
                    # Add rightward force impulse
                    impulse_force = np.array([FORCE_MAGNITUDE, 0])
                    self.force_impulses.append((impulse_force, self.impulse_duration))

        return True

    def update(self):
        """Update game state."""
        # Update force impulses (decrease remaining frames)
        updated_impulses = []
        for force_vector, remaining_frames in self.force_impulses:
            remaining_frames -= 1
            if remaining_frames > 0:
                updated_impulses.append((force_vector, remaining_frames))
        self.force_impulses = updated_impulses
        
        if self.game_state == "playing":
            prev_pos = self.ball.pos.copy()
            self.ball.update(self.physics_engine, self.applied_force)
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

        # Draw ball with direction indicator
        ball_screen_x, ball_screen_y = self.ball.get_screen_pos()
        ball_radius_pixels = int(BALL_RADIUS * PIXELS_PER_METER)
        
        # Draw main ball
        pygame.draw.circle(self.screen, YELLOW, (ball_screen_x, ball_screen_y),
                          ball_radius_pixels)
        pygame.draw.circle(self.screen, BLACK, (ball_screen_x, ball_screen_y),
                          ball_radius_pixels, 2)
        
        # Draw direction arrow
        arrow_length = ball_radius_pixels * 0.8
        arrow_end_x = (ball_screen_x + int(arrow_length *
                                          np.cos(self.ball.rotation)))
        arrow_end_y = (ball_screen_y - int(arrow_length *
                                          np.sin(self.ball.rotation)))
        
        # Draw arrow line
        pygame.draw.line(self.screen, RED, (ball_screen_x, ball_screen_y),
                        (arrow_end_x, arrow_end_y), 3)
        
        # Draw arrow head
        arrow_head_size = 5
        head_angle1 = self.ball.rotation + 2.5  # 2.5 radians ≈ 143 degrees
        head_angle2 = self.ball.rotation - 2.5
        
        head1_x = arrow_end_x + int(arrow_head_size * np.cos(head_angle1))
        head1_y = arrow_end_y - int(arrow_head_size * np.sin(head_angle1))
        head2_x = arrow_end_x + int(arrow_head_size * np.cos(head_angle2))
        head2_y = arrow_end_y - int(arrow_head_size * np.sin(head_angle2))
        
        pygame.draw.polygon(self.screen, RED, [
            (arrow_end_x, arrow_end_y),
            (head1_x, head1_y),
            (head2_x, head2_y)
        ])

        # Draw force vector
        if np.linalg.norm(self.applied_force) > 0.1:
            force_scale = 0.5
            force_end_x = ball_screen_x + int(self.applied_force[0] *
                                             force_scale)
            force_end_y = ball_screen_y - int(self.applied_force[1] *
                                             force_scale)
            pygame.draw.line(self.screen, ORANGE, (ball_screen_x, ball_screen_y),
                           (force_end_x, force_end_y), 3)

        self.draw_ui()
        pygame.display.flip()

    def draw_ui(self):
        """Draw user interface elements."""
        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        self.screen.blit(score_text, (10, 10))

        instructions = [
            "WASD: Apply forces to ball",
            "R: Reset game",
            "ESC: Quit"
        ]
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, BLACK)
            self.screen.blit(text, (10, 50 + i * 25))

        if self.game_state == "scored":
            goal_text = self.font.render("GOAL!", True, GREEN)
            text_rect = goal_text.get_rect(center=(SCREEN_WIDTH//2, 100))
            self.screen.blit(goal_text, text_rect)

        pos_text = self.small_font.render(
            f"Position: ({self.ball.pos[0]:.2f}, {self.ball.pos[1]:.2f}) m",
            True, BLACK)
        vel_text = self.small_font.render(
            f"Velocity: ({self.ball.vel[0]:.2f}, {self.ball.vel[1]:.2f}) m/s",
            True, BLACK)
        angular_text = self.small_font.render(
            f"Angular Vel: {self.ball.angular_vel:.2f} rad/s",
            True, BLACK)
        rotation_text = self.small_font.render(
            f"Rotation: {self.ball.rotation:.2f} rad",
            True, BLACK)
        impulse_text = self.small_font.render(
            f"Active impulses: {len(self.force_impulses)}",
            True, BLACK)
        
        # Add friction state info
        ground_y_meters = GROUND_Y / PIXELS_PER_METER
        if self.ball.pos[1] <= ground_y_meters + BALL_RADIUS:
            expected_angular_vel = -self.ball.vel[0] / BALL_RADIUS
            angular_vel_diff = abs(self.ball.angular_vel - expected_angular_vel)
            is_rolling = angular_vel_diff < 0.1 and abs(self.ball.vel[0]) > 0.01
            friction_state = "Rolling" if is_rolling else "Sliding"
        else:
            friction_state = "In Air"
        
        friction_text = self.small_font.render(
            f"State: {friction_state}",
            True, BLACK)
        
        self.screen.blit(pos_text, (10, SCREEN_HEIGHT - 135))
        self.screen.blit(vel_text, (10, SCREEN_HEIGHT - 110))
        self.screen.blit(angular_text, (10, SCREEN_HEIGHT - 85))
        self.screen.blit(rotation_text, (10, SCREEN_HEIGHT - 60))
        self.screen.blit(friction_text, (10, SCREEN_HEIGHT - 35))
        self.screen.blit(impulse_text, (10, SCREEN_HEIGHT - 10))

    def reset_game(self):
        """Reset the game to initial state."""
        initial_x = 2.0
        initial_y = GROUND_Y / PIXELS_PER_METER + BALL_RADIUS  # On ground
        self.ball.reset(initial_x, initial_y)
        self.game_state = "playing"
        self.force_impulses = []  # Clear all force impulses

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
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
