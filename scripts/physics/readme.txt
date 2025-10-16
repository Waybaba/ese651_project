Assignment: Interactive Simulator

Task:
Design an interactive simulator in which you can apply forces to a ball using your keyboard to shoot it toward a vertical goal line segment floating in the air.

Scene Description

A ball is placed on the ground at some initial position near the origin of a 2D plane.

A vertical goal line segment is placed in front of the ball:

The segment has a fixed x-coordinate (e.g., x = X_goal).

Its y-coordinate spans a vertical range from y_min to y_max.

The ball must cross this line segment to score.

The coordinate system:

x-axis → horizontal (rightward)

y-axis → vertical (upward)

You can use the keyboard to apply forces:

W → Up (+y direction)

S → Down (−y direction)

A → Left (−x direction)

D → Right (+x direction)

Illustration (ASCII Diagram)
                     ↑ y
                     |
           y_max     ●
                     │
                     │  Goal segment
                     │  (x = X_goal,
                     │   y ∈ [y_min, y_max])
           y_min     ●
                     |
Ball  O--------------+--------------------→ x
                    Ground
         ↑W
 A ←    [O]    → D
         ↓S


The goal is a vertical line segment located at a fixed horizontal position x = X_goal, and extends vertically from y_min to y_max.
To score, the ball’s trajectory must intersect this segment.

Rules

You receive a passing ball from a teammate.

You must shoot the ball starting at least 1 meter away from the goal (along the x-axis).

Use the keyboard to apply forces to the ball and control its trajectory.

You score a goal if the ball crosses x = X_goal with its y coordinate in the range [y_min, y_max].

Bonus Points

Extra credit if you submit:

Your code for the simulator.

A short video of yourself playing (showing your hand on the keyboard and your laptop screen).

Additional points if you successfully score a goal in the video.