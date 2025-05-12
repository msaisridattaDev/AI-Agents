"""
Simple AI Agent implementation.
"""
import random
from typing import Dict, List, Any, Tuple


class Agent:
    """
    A simple AI agent that can perceive its environment, make decisions, and take actions.
    """
    
    def __init__(self, name: str, capabilities: List[str] = None):
        """
        Initialize the agent with a name and optional capabilities.
        
        Args:
            name: The name of the agent
            capabilities: List of capabilities the agent has
        """
        self.name = name
        self.capabilities = capabilities or ["observe", "decide", "act"]
        self.memory = []
        self.state = {}
        self.rules = {}
        self.learning_rate = 0.1
        self.exploration_rate = 0.2
        self.action_values = {}  # For simple reinforcement learning
        
        print(f"Agent '{self.name}' initialized with capabilities: {self.capabilities}")
    
    def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perceive the environment and update the agent's state.
        
        Args:
            environment: Dictionary representing the environment state
            
        Returns:
            Dictionary of perceived information
        """
        perception = {}
        
        # Extract relevant information from the environment
        for key, value in environment.items():
            if key in self.capabilities or "observe" in self.capabilities:
                perception[key] = value
        
        # Update agent's state with new perceptions
        self.state.update(perception)
        
        # Store in memory
        self.memory.append(("perception", perception))
        if len(self.memory) > 100:  # Limit memory size
            self.memory.pop(0)
            
        return perception
    
    def decide(self) -> str:
        """
        Make a decision based on the current state.
        
        Returns:
            The decision (action to take)
        """
        available_actions = self.state.get("available_actions", ["wait"])
        
        # Decision making strategies
        if random.random() < self.exploration_rate:
            # Exploration: try random actions sometimes
            decision = random.choice(available_actions)
        else:
            # Exploitation: use learned values or rules
            if self.action_values and all(action in self.action_values for action in available_actions):
                # Use learned action values
                decision = max(available_actions, key=lambda a: self.action_values.get(a, 0))
            else:
                # Use rules if defined
                for condition, action in self.rules.items():
                    if self._evaluate_condition(condition):
                        decision = action
                        break
                else:
                    # Default to random choice if no rule matches
                    decision = random.choice(available_actions)
        
        # Store decision in memory
        self.memory.append(("decision", decision))
        
        return decision
    
    def act(self, action: str, environment: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Execute an action in the environment.
        
        Args:
            action: The action to take
            environment: The environment to act upon
            
        Returns:
            Tuple of (result message, updated environment)
        """
        # Check if the action is valid
        available_actions = environment.get("available_actions", ["wait"])
        if action not in available_actions and "act" in self.capabilities:
            return f"Cannot perform action '{action}'. Available actions: {available_actions}", environment
        
        # Execute the action (in a real system, this would modify the environment)
        result_message = f"Executed action: {action}"
        
        # In this simple implementation, we'll just modify the environment slightly
        # based on the action
        updated_environment = environment.copy()
        
        if action == "move_forward":
            updated_environment["position"] = (
                environment.get("position", (0, 0))[0] + 1,
                environment.get("position", (0, 0))[1]
            )
        elif action == "move_backward":
            updated_environment["position"] = (
                environment.get("position", (0, 0))[0] - 1,
                environment.get("position", (0, 0))[1]
            )
        elif action == "turn_left":
            updated_environment["orientation"] = "left"
        elif action == "turn_right":
            updated_environment["orientation"] = "right"
        
        # Store action in memory
        self.memory.append(("action", action))
        
        return result_message, updated_environment
    
    def learn(self, reward: float, state: Dict[str, Any], action: str) -> None:
        """
        Update the agent's knowledge based on rewards received.
        
        Args:
            reward: The reward value for the last action
            state: The state in which the action was taken
            action: The action that was taken
        """
        # Simple Q-learning update
        state_key = self._state_to_key(state)
        state_action_key = f"{state_key}:{action}"
        
        # Initialize if not exists
        if state_action_key not in self.action_values:
            self.action_values[state_action_key] = 0.0
            
        # Update action value
        current_value = self.action_values[state_action_key]
        self.action_values[state_action_key] = current_value + self.learning_rate * (reward - current_value)
        
        # Reduce exploration rate over time (simple decay)
        self.exploration_rate = max(0.05, self.exploration_rate * 0.99)
        
        # Store learning in memory
        self.memory.append(("learning", {
            "state": state_key,
            "action": action,
            "reward": reward,
            "new_value": self.action_values[state_action_key]
        }))
    
    def add_rule(self, condition: str, action: str) -> None:
        """
        Add a rule to the agent's decision-making process.
        
        Args:
            condition: A condition string (will be evaluated)
            action: The action to take when the condition is true
        """
        self.rules[condition] = action
        print(f"Added rule: IF {condition} THEN {action}")
    
    def _evaluate_condition(self, condition: str) -> bool:
        """
        Evaluate a condition string against the current state.
        
        Args:
            condition: Condition string to evaluate
            
        Returns:
            Boolean result of evaluation
        """
        # This is a simplified implementation
        # In a real system, you might use a proper expression evaluator
        
        # Example conditions:
        # "position[0] > 5"
        # "orientation == 'left'"
        
        try:
            # Create a dictionary of variables for evaluation
            variables = {}
            for key, value in self.state.items():
                variables[key] = value
            
            # Evaluate the condition in the context of the variables
            return eval(condition, {"__builtins__": {}}, variables)
        except:
            return False
    
    def _state_to_key(self, state: Dict[str, Any]) -> str:
        """
        Convert a state dictionary to a string key for storage.
        
        Args:
            state: The state dictionary
            
        Returns:
            String representation of the state
        """
        # This is a simplified implementation
        # In a real system, you might use a more sophisticated state representation
        return str(sorted(state.items()))
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.
        
        Returns:
            Dictionary with agent status information
        """
        return {
            "name": self.name,
            "capabilities": self.capabilities,
            "state": self.state,
            "memory_size": len(self.memory),
            "rules": len(self.rules),
            "exploration_rate": self.exploration_rate
        }
