"""
Enhanced AI Agent implementation using machine learning models.
"""
import random
from typing import Dict, List, Any, Tuple
import numpy as np

from agent import Agent
from models.simple_model import SimpleModel


class EnhancedAgent(Agent):
    """
    An enhanced AI agent that uses machine learning for decision making.
    """
    
    def __init__(self, name: str, capabilities: List[str] = None):
        """
        Initialize the enhanced agent.
        
        Args:
            name: The name of the agent
            capabilities: List of capabilities the agent has
        """
        super().__init__(name, capabilities)
        
        # Add machine learning model
        self.model = SimpleModel()
        
        # Add more sophisticated learning parameters
        self.gamma = 0.95  # Discount factor for future rewards
        self.epsilon = 0.2  # Initial exploration rate
        self.epsilon_decay = 0.995  # Decay rate for exploration
        self.epsilon_min = 0.01  # Minimum exploration rate
        
        # Add experience replay buffer
        self.experiences = []
        self.max_experiences = 1000
        self.batch_size = 32
        
        print(f"Enhanced Agent '{self.name}' initialized with ML capabilities")
    
    def decide(self) -> str:
        """
        Make a decision based on the current state using the ML model.
        
        Returns:
            The decision (action to take)
        """
        available_actions = self.state.get("available_actions", ["wait"])
        
        # Exploration: try random actions sometimes
        if random.random() < self.epsilon:
            decision = random.choice(available_actions)
        else:
            # Exploitation: use the model to predict the best action
            decision = self.model.predict(self.state)
            
            # Make sure the decision is in available actions
            if decision not in available_actions:
                decision = random.choice(available_actions)
        
        # Store decision in memory
        self.memory.append(("decision", decision))
        
        return decision
    
    def learn(self, reward: float, state: Dict[str, Any], action: str) -> None:
        """
        Update the agent's knowledge based on rewards received.
        
        Args:
            reward: The reward value for the last action
            state: The state in which the action was taken
            action: The action that was taken
        """
        # Store experience in replay buffer
        experience = (state, action, reward, self.state.copy())
        self.experiences.append(experience)
        
        # Limit buffer size
        if len(self.experiences) > self.max_experiences:
            self.experiences.pop(0)
        
        # Update model with current experience
        target = reward
        if "goal_position" in self.state and self.state["position"] != self.state["goal_position"]:
            # If not at goal, include future rewards in target
            next_state_values = self.model.get_all_action_values(self.state)
            max_next_value = max(next_state_values.values()) if next_state_values else 0
            target += self.gamma * max_next_value
        
        self.model.update(state, action, target)
        
        # Batch learning from replay buffer
        if len(self.experiences) >= self.batch_size:
            self._learn_from_batch()
        
        # Decay exploration rate
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        # Store learning in memory
        self.memory.append(("learning", {
            "state": str(state),
            "action": action,
            "reward": reward,
            "epsilon": self.epsilon
        }))
    
    def _learn_from_batch(self) -> None:
        """
        Learn from a batch of experiences.
        """
        # Sample a batch of experiences
        batch = random.sample(self.experiences, self.batch_size)
        
        for state, action, reward, next_state in batch:
            target = reward
            
            # If not at goal, include future rewards in target
            if "goal_position" in next_state and next_state["position"] != next_state["goal_position"]:
                next_state_values = self.model.get_all_action_values(next_state)
                max_next_value = max(next_state_values.values()) if next_state_values else 0
                target += self.gamma * max_next_value
            
            # Update model
            self.model.update(state, action, target)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.
        
        Returns:
            Dictionary with agent status information
        """
        status = super().get_status()
        
        # Add enhanced agent specific information
        status.update({
            "epsilon": self.epsilon,
            "experiences": len(self.experiences),
            "model_type": type(self.model).__name__
        })
        
        return status
