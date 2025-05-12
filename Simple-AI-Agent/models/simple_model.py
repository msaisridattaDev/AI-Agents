"""
Simple machine learning model for the AI agent.
"""
import numpy as np
from typing import Dict, List, Tuple, Any
from sklearn.linear_model import SGDRegressor


class SimpleModel:
    """
    A simple machine learning model for the AI agent.
    """
    
    def __init__(self, state_size: int = 10, action_size: int = 5):
        """
        Initialize the model.
        
        Args:
            state_size: Size of the state vector
            action_size: Number of possible actions
        """
        self.state_size = state_size
        self.action_size = action_size
        
        # Create a regressor for each action
        self.models = [SGDRegressor(learning_rate='constant', eta0=0.01) 
                      for _ in range(action_size)]
        
        # Initialize models with dummy data
        dummy_X = np.zeros((1, state_size))
        dummy_y = np.zeros(1)
        for model in self.models:
            model.partial_fit(dummy_X, dummy_y)
        
        self.action_map = {
            "move_forward": 0,
            "move_backward": 1,
            "turn_left": 2,
            "turn_right": 3,
            "wait": 4
        }
        
        self.inverse_action_map = {v: k for k, v in self.action_map.items()}
    
    def state_to_vector(self, state: Dict[str, Any]) -> np.ndarray:
        """
        Convert a state dictionary to a feature vector.
        
        Args:
            state: The state dictionary
            
        Returns:
            Feature vector representation of the state
        """
        # Extract relevant features from the state
        position = state.get("position", (0, 0))
        orientation = state.get("orientation", "right")
        goal_position = state.get("goal_position", (0, 0))
        
        # Convert orientation to one-hot encoding
        orientation_one_hot = [0, 0, 0, 0]  # right, left, up, down
        if orientation == "right":
            orientation_one_hot[0] = 1
        elif orientation == "left":
            orientation_one_hot[1] = 1
        elif orientation == "up":
            orientation_one_hot[2] = 1
        elif orientation == "down":
            orientation_one_hot[3] = 1
        
        # Calculate distance to goal
        distance_x = goal_position[0] - position[0]
        distance_y = goal_position[1] - position[1]
        
        # Create feature vector
        features = [
            position[0],
            position[1],
            *orientation_one_hot,
            distance_x,
            distance_y,
            abs(distance_x),
            abs(distance_y)
        ]
        
        # Pad or truncate to match state_size
        if len(features) < self.state_size:
            features.extend([0] * (self.state_size - len(features)))
        elif len(features) > self.state_size:
            features = features[:self.state_size]
        
        return np.array(features).reshape(1, -1)
    
    def predict(self, state: Dict[str, Any]) -> str:
        """
        Predict the best action for a given state.
        
        Args:
            state: The state dictionary
            
        Returns:
            The predicted best action
        """
        # Convert state to feature vector
        X = self.state_to_vector(state)
        
        # Get predictions for each action
        predictions = [model.predict(X)[0] for model in self.models]
        
        # Get the action with the highest predicted value
        best_action_idx = np.argmax(predictions)
        
        # Convert back to action string
        return self.inverse_action_map.get(best_action_idx, "wait")
    
    def update(self, state: Dict[str, Any], action: str, target: float) -> None:
        """
        Update the model with a new experience.
        
        Args:
            state: The state dictionary
            action: The action taken
            target: The target value (reward + future value)
        """
        # Convert state to feature vector
        X = self.state_to_vector(state)
        
        # Get the action index
        action_idx = self.action_map.get(action, 4)  # Default to "wait"
        
        # Update the corresponding model
        self.models[action_idx].partial_fit(X, [target])
    
    def get_all_action_values(self, state: Dict[str, Any]) -> Dict[str, float]:
        """
        Get the predicted values for all actions in a given state.
        
        Args:
            state: The state dictionary
            
        Returns:
            Dictionary mapping actions to their predicted values
        """
        # Convert state to feature vector
        X = self.state_to_vector(state)
        
        # Get predictions for each action
        predictions = [model.predict(X)[0] for model in self.models]
        
        # Create a dictionary mapping actions to values
        return {self.inverse_action_map[i]: value for i, value in enumerate(predictions)}
