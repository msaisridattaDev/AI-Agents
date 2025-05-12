"""
Simple environment for the AI agent to operate in.
"""
from typing import Dict, Any, Tuple, List
import random


class Environment:
    """
    A simple environment that the agent can interact with.
    """
    
    def __init__(self, size: Tuple[int, int] = (10, 10)):
        """
        Initialize the environment.
        
        Args:
            size: The size of the environment grid (width, height)
        """
        self.size = size
        self.state = {
            "position": (0, 0),
            "orientation": "right",
            "objects": {},
            "available_actions": ["move_forward", "move_backward", "turn_left", "turn_right", "wait"],
            "goal_position": (size[0] - 1, size[1] - 1),
            "obstacles": []
        }
        
        # Add some random obstacles
        num_obstacles = random.randint(3, 10)
        for _ in range(num_obstacles):
            obstacle_pos = (random.randint(1, size[0] - 2), random.randint(1, size[1] - 2))
            # Make sure obstacles don't block the start or goal
            if obstacle_pos != (0, 0) and obstacle_pos != self.state["goal_position"]:
                self.state["obstacles"].append(obstacle_pos)
        
        print(f"Environment initialized with size {size} and {len(self.state['obstacles'])} obstacles")
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the environment.
        
        Returns:
            Dictionary representing the environment state
        """
        return self.state.copy()
    
    def update(self, action: str) -> Tuple[Dict[str, Any], float, bool]:
        """
        Update the environment based on an action.
        
        Args:
            action: The action to perform
            
        Returns:
            Tuple of (new state, reward, done)
        """
        # Copy the current state
        new_state = self.state.copy()
        reward = -0.1  # Small negative reward for each step (encourages efficiency)
        done = False
        
        # Get current position and orientation
        position = new_state["position"]
        orientation = new_state["orientation"]
        
        # Process the action
        if action == "move_forward":
            # Calculate new position based on orientation
            if orientation == "right":
                new_position = (position[0] + 1, position[1])
            elif orientation == "left":
                new_position = (position[0] - 1, position[1])
            elif orientation == "up":
                new_position = (position[0], position[1] - 1)
            elif orientation == "down":
                new_position = (position[0], position[1] + 1)
            else:
                new_position = position
            
            # Check if the new position is valid
            if self._is_valid_position(new_position):
                new_state["position"] = new_position
            else:
                reward -= 1.0  # Penalty for hitting a wall or obstacle
        
        elif action == "move_backward":
            # Calculate new position based on orientation
            if orientation == "right":
                new_position = (position[0] - 1, position[1])
            elif orientation == "left":
                new_position = (position[0] + 1, position[1])
            elif orientation == "up":
                new_position = (position[0], position[1] + 1)
            elif orientation == "down":
                new_position = (position[0], position[1] - 1)
            else:
                new_position = position
            
            # Check if the new position is valid
            if self._is_valid_position(new_position):
                new_state["position"] = new_position
            else:
                reward -= 1.0  # Penalty for hitting a wall or obstacle
        
        elif action == "turn_left":
            # Update orientation
            if orientation == "right":
                new_state["orientation"] = "up"
            elif orientation == "up":
                new_state["orientation"] = "left"
            elif orientation == "left":
                new_state["orientation"] = "down"
            elif orientation == "down":
                new_state["orientation"] = "right"
        
        elif action == "turn_right":
            # Update orientation
            if orientation == "right":
                new_state["orientation"] = "down"
            elif orientation == "down":
                new_state["orientation"] = "left"
            elif orientation == "left":
                new_state["orientation"] = "up"
            elif orientation == "up":
                new_state["orientation"] = "right"
        
        # Check if the agent reached the goal
        if new_state["position"] == new_state["goal_position"]:
            reward += 10.0  # Big reward for reaching the goal
            done = True
        
        # Update the state
        self.state = new_state
        
        return new_state.copy(), reward, done
    
    def _is_valid_position(self, position: Tuple[int, int]) -> bool:
        """
        Check if a position is valid (within bounds and not an obstacle).
        
        Args:
            position: The position to check
            
        Returns:
            True if the position is valid, False otherwise
        """
        # Check if the position is within bounds
        if (position[0] < 0 or position[0] >= self.size[0] or
            position[1] < 0 or position[1] >= self.size[1]):
            return False
        
        # Check if the position is an obstacle
        if position in self.state["obstacles"]:
            return False
        
        return True
    
    def reset(self) -> Dict[str, Any]:
        """
        Reset the environment to its initial state.
        
        Returns:
            The initial state
        """
        # Reset position and orientation
        self.state["position"] = (0, 0)
        self.state["orientation"] = "right"
        
        # Randomize goal position (but keep it on the edge)
        edge = random.choice(["right", "bottom"])
        if edge == "right":
            self.state["goal_position"] = (self.size[0] - 1, random.randint(0, self.size[1] - 1))
        else:
            self.state["goal_position"] = (random.randint(0, self.size[0] - 1), self.size[1] - 1)
        
        # Randomize obstacles
        self.state["obstacles"] = []
        num_obstacles = random.randint(3, 10)
        for _ in range(num_obstacles):
            obstacle_pos = (random.randint(1, self.size[0] - 2), random.randint(1, self.size[1] - 2))
            # Make sure obstacles don't block the start or goal
            if obstacle_pos != (0, 0) and obstacle_pos != self.state["goal_position"]:
                self.state["obstacles"].append(obstacle_pos)
        
        return self.state.copy()
    
    def render(self) -> str:
        """
        Render the environment as a string.
        
        Returns:
            String representation of the environment
        """
        # Create a grid representation
        grid = [[' ' for _ in range(self.size[0])] for _ in range(self.size[1])]
        
        # Add obstacles
        for x, y in self.state["obstacles"]:
            if 0 <= x < self.size[0] and 0 <= y < self.size[1]:
                grid[y][x] = 'X'
        
        # Add goal
        goal_x, goal_y = self.state["goal_position"]
        if 0 <= goal_x < self.size[0] and 0 <= goal_y < self.size[1]:
            grid[goal_y][goal_x] = 'G'
        
        # Add agent
        agent_x, agent_y = self.state["position"]
        if 0 <= agent_x < self.size[0] and 0 <= agent_y < self.size[1]:
            # Use different characters based on orientation
            if self.state["orientation"] == "right":
                grid[agent_y][agent_x] = '>'
            elif self.state["orientation"] == "left":
                grid[agent_y][agent_x] = '<'
            elif self.state["orientation"] == "up":
                grid[agent_y][agent_x] = '^'
            elif self.state["orientation"] == "down":
                grid[agent_y][agent_x] = 'v'
        
        # Convert grid to string
        result = ""
        for row in grid:
            result += '|' + ''.join(row) + '|\n'
        
        # Add legend
        result += "\nLegend:\n"
        result += "  > < ^ v : Agent (facing right, left, up, down)\n"
        result += "  X : Obstacle\n"
        result += "  G : Goal\n"
        
        return result
