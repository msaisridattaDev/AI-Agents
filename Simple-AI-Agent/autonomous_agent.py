"""
Autonomous AI Agent implementation with planning capabilities.
"""
import random
import time
import heapq
from typing import Dict, List, Any, Tuple, Set, Optional
import numpy as np

from agent import Agent


class AutonomousAgent(Agent):
    """
    An autonomous AI agent with planning capabilities and goal-oriented behavior.
    """
    
    def __init__(self, name: str, capabilities: List[str] = None):
        """
        Initialize the autonomous agent.
        
        Args:
            name: The name of the agent
            capabilities: List of capabilities the agent has
        """
        # Add planning to capabilities
        if capabilities is None:
            capabilities = ["observe", "decide", "act", "plan"]
        elif "plan" not in capabilities:
            capabilities.append("plan")
            
        super().__init__(name, capabilities)
        
        # Planning parameters
        self.has_goal = False
        self.current_plan = []
        self.known_map = {}  # Discovered environment cells
        self.visited_positions = set()
        self.goal_position = None
        self.planning_horizon = 20  # How far ahead to plan
        self.replanning_frequency = 5  # How often to replan
        self.step_counter = 0
        self.thinking_process = []  # Store agent's reasoning for transparency
        
        # Autonomous operation parameters
        self.is_autonomous = False
        self.autonomous_sleep_time = 0.5  # Time between autonomous actions
        self.max_autonomous_steps = 200  # Maximum steps in autonomous mode
        self.autonomous_step_counter = 0
        
        print(f"Autonomous Agent '{self.name}' initialized with planning capabilities")
    
    def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perceive the environment and update the agent's internal map.
        
        Args:
            environment: Dictionary representing the environment state
            
        Returns:
            Dictionary of perceived information
        """
        perception = super().perceive(environment)
        
        # Update the agent's knowledge of the environment
        if "position" in environment:
            current_pos = environment["position"]
            self.visited_positions.add(current_pos)
            
            # Update known map with current position
            self.known_map[current_pos] = "empty"
            
            # Update goal position if available
            if "goal_position" in environment:
                self.goal_position = environment["goal_position"]
                self.has_goal = True
                self.known_map[environment["goal_position"]] = "goal"
            
            # Update obstacles in the map
            if "obstacles" in environment:
                for obstacle_pos in environment["obstacles"]:
                    self.known_map[obstacle_pos] = "obstacle"
        
        # Add thinking process
        self.thinking_process.append({
            "type": "perception",
            "position": environment.get("position"),
            "orientation": environment.get("orientation"),
            "known_map_size": len(self.known_map)
        })
        
        return perception
    
    def decide(self) -> str:
        """
        Make a decision based on planning and current state.
        
        Returns:
            The decision (action to take)
        """
        self.step_counter += 1
        
        # Check if we need to replan
        if not self.current_plan or self.step_counter % self.replanning_frequency == 0:
            self._plan()
        
        # Get the next action from the plan
        if self.current_plan:
            decision = self.current_plan.pop(0)
        else:
            # If no plan, use exploration strategy
            decision = self._explore()
        
        # Store decision in memory and thinking process
        self.memory.append(("decision", decision))
        self.thinking_process.append({
            "type": "decision",
            "action": decision,
            "remaining_plan_steps": len(self.current_plan),
            "step_counter": self.step_counter
        })
        
        return decision
    
    def _plan(self) -> None:
        """
        Create a plan to reach the goal using A* pathfinding.
        """
        if not self.has_goal or "position" not in self.state:
            self.thinking_process.append({
                "type": "planning",
                "result": "failed",
                "reason": "No goal or position information available"
            })
            return
        
        start_pos = self.state["position"]
        goal_pos = self.goal_position
        
        # If we're at the goal, no need to plan
        if start_pos == goal_pos:
            self.current_plan = []
            self.thinking_process.append({
                "type": "planning",
                "result": "success",
                "plan": "Already at goal"
            })
            return
        
        # A* pathfinding
        path = self._a_star_search(start_pos, goal_pos)
        
        if path:
            # Convert path to actions
            self.current_plan = self._path_to_actions(path)
            self.thinking_process.append({
                "type": "planning",
                "result": "success",
                "plan_length": len(self.current_plan),
                "path": path
            })
        else:
            # If no path found, plan for exploration
            self.current_plan = [self._explore() for _ in range(self.planning_horizon)]
            self.thinking_process.append({
                "type": "planning",
                "result": "exploration",
                "plan_length": len(self.current_plan)
            })
    
    def _a_star_search(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        A* search algorithm to find a path from start to goal.
        
        Args:
            start: Starting position (x, y)
            goal: Goal position (x, y)
            
        Returns:
            List of positions forming a path, or empty list if no path found
        """
        # Priority queue for A*
        open_set = [(0, start)]  # (f_score, position)
        came_from = {}
        
        # Cost from start to current position
        g_score = {start: 0}
        
        # Estimated total cost from start to goal through current position
        f_score = {start: self._heuristic(start, goal)}
        
        # Set of visited nodes
        closed_set = set()
        
        while open_set:
            # Get the position with the lowest f_score
            current_f, current = heapq.heappop(open_set)
            
            if current in closed_set:
                continue
                
            closed_set.add(current)
            
            # If we reached the goal, reconstruct the path
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path
            
            # Check all neighbors
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Skip if neighbor is an obstacle or out of bounds
                if (neighbor in self.known_map and self.known_map[neighbor] == "obstacle" or
                    neighbor[0] < 0 or neighbor[1] < 0 or
                    neighbor[0] >= 10 or neighbor[1] >= 10):  # Assuming 10x10 grid
                    continue
                
                # Calculate tentative g_score
                tentative_g_score = g_score[current] + 1
                
                # If this path is better than any previous one
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        # No path found
        return []
    
    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """
        Manhattan distance heuristic for A*.
        
        Args:
            a: First position
            b: Second position
            
        Returns:
            Manhattan distance between positions
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def _path_to_actions(self, path: List[Tuple[int, int]]) -> List[str]:
        """
        Convert a path to a sequence of actions.
        
        Args:
            path: List of positions forming a path
            
        Returns:
            List of actions to follow the path
        """
        if not path or len(path) < 2:
            return []
        
        actions = []
        current_pos = path[0]
        current_orientation = self.state.get("orientation", "right")
        
        for next_pos in path[1:]:
            # Determine direction to next position
            dx = next_pos[0] - current_pos[0]
            dy = next_pos[1] - current_pos[1]
            
            # Determine target orientation
            target_orientation = current_orientation
            if dx > 0:
                target_orientation = "right"
            elif dx < 0:
                target_orientation = "left"
            elif dy > 0:
                target_orientation = "down"
            elif dy < 0:
                target_orientation = "up"
            
            # Add actions to turn to the target orientation
            while current_orientation != target_orientation:
                if self._is_clockwise_turn(current_orientation, target_orientation):
                    actions.append("turn_right")
                    current_orientation = self._get_orientation_after_turn(current_orientation, "right")
                else:
                    actions.append("turn_left")
                    current_orientation = self._get_orientation_after_turn(current_orientation, "left")
            
            # Add action to move forward
            actions.append("move_forward")
            
            # Update current position
            current_pos = next_pos
        
        return actions
    
    def _is_clockwise_turn(self, from_orientation: str, to_orientation: str) -> bool:
        """
        Determine if turning from one orientation to another is clockwise.
        
        Args:
            from_orientation: Starting orientation
            to_orientation: Target orientation
            
        Returns:
            True if the turn is clockwise, False otherwise
        """
        orientations = ["up", "right", "down", "left"]
        from_index = orientations.index(from_orientation)
        to_index = orientations.index(to_orientation)
        
        # Calculate the difference, considering the circular nature
        diff = (to_index - from_index) % 4
        
        # If diff is 1 or 2, it's a clockwise turn
        return diff == 1 or diff == 2
    
    def _get_orientation_after_turn(self, orientation: str, turn_direction: str) -> str:
        """
        Get the new orientation after turning.
        
        Args:
            orientation: Current orientation
            turn_direction: Direction to turn ("left" or "right")
            
        Returns:
            New orientation after turning
        """
        orientations = ["up", "right", "down", "left"]
        current_index = orientations.index(orientation)
        
        if turn_direction == "right":
            return orientations[(current_index + 1) % 4]
        else:  # turn_direction == "left"
            return orientations[(current_index - 1) % 4]
    
    def _explore(self) -> str:
        """
        Decide on an exploration action when no plan is available.
        
        Returns:
            Action for exploration
        """
        available_actions = self.state.get("available_actions", ["move_forward", "turn_left", "turn_right", "wait"])
        
        # Prefer moving forward if possible
        if "move_forward" in available_actions and random.random() < 0.7:
            return "move_forward"
        
        # Otherwise, turn to explore new areas
        if "turn_left" in available_actions and "turn_right" in available_actions:
            return random.choice(["turn_left", "turn_right"])
        elif "turn_left" in available_actions:
            return "turn_left"
        elif "turn_right" in available_actions:
            return "turn_right"
        
        # If nothing else is available, wait
        return "wait"
    
    def run_autonomously(self, environment, update_callback=None, max_steps=None) -> Dict[str, Any]:
        """
        Run the agent autonomously for a number of steps or until goal is reached.
        
        Args:
            environment: The environment to run in
            update_callback: Callback function to update UI after each step
            max_steps: Maximum number of steps to run (defaults to self.max_autonomous_steps)
            
        Returns:
            Dictionary with run statistics
        """
        if max_steps is None:
            max_steps = self.max_autonomous_steps
            
        self.is_autonomous = True
        self.autonomous_step_counter = 0
        
        state = environment.get_state()
        done = False
        total_reward = 0
        
        while not done and self.autonomous_step_counter < max_steps:
            # Perceive the environment
            self.perceive(state)
            
            # Decide on an action
            action = self.decide()
            
            # Act in the environment
            self.act(action, state)
            
            # Update the environment
            new_state, reward, done = environment.update(action)
            
            # Update statistics
            total_reward += reward
            self.autonomous_step_counter += 1
            
            # Update state
            state = new_state
            
            # Call the update callback if provided
            if update_callback:
                update_callback(state, action, reward, done, total_reward)
            
            # Small delay for visualization
            time.sleep(self.autonomous_sleep_time)
        
        self.is_autonomous = False
        
        # Return run statistics
        return {
            "steps": self.autonomous_step_counter,
            "total_reward": total_reward,
            "goal_reached": done
        }
    
    def get_thinking_process(self) -> List[Dict[str, Any]]:
        """
        Get the agent's thinking process for transparency.
        
        Returns:
            List of thinking steps with details
        """
        return self.thinking_process
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.
        
        Returns:
            Dictionary with agent status information
        """
        status = super().get_status()
        
        # Add autonomous agent specific information
        status.update({
            "has_goal": self.has_goal,
            "plan_length": len(self.current_plan),
            "known_map_size": len(self.known_map),
            "visited_positions": len(self.visited_positions),
            "is_autonomous": self.is_autonomous,
            "autonomous_steps": self.autonomous_step_counter
        })
        
        return status
