"""
Script to train the AI agent.
"""
import argparse
import time
import pickle
from typing import Dict, List, Any

from agent import Agent
from enhanced_agent import EnhancedAgent
from environment import Environment
from utils.visualization import plot_learning_curve, plot_action_values


def train_agent(agent_type: str, episodes: int = 100, max_steps: int = 100, 
               render: bool = False, save_path: str = None) -> Dict[str, Any]:
    """
    Train an agent for a specified number of episodes.
    
    Args:
        agent_type: Type of agent to train ('basic' or 'enhanced')
        episodes: Number of episodes to train for
        max_steps: Maximum steps per episode
        render: Whether to render the environment during training
        save_path: Path to save the trained agent
        
    Returns:
        Dictionary with training statistics
    """
    # Create agent based on type
    if agent_type.lower() == 'enhanced':
        agent = EnhancedAgent("TrainedAgent")
    else:
        agent = Agent("TrainedAgent")
    
    # Create environment
    environment = Environment(size=(10, 10))
    
    # Training statistics
    episode_rewards = []
    episode_steps = []
    goals_reached = 0
    
    # Train for specified number of episodes
    for episode in range(episodes):
        # Reset the environment
        state = environment.reset()
        
        total_reward = 0
        steps = 0
        done = False
        
        # Run until done or max steps reached
        while not done and steps < max_steps:
            # Render the environment
            if render and episode % 10 == 0:  # Render every 10th episode
                print("\n" + environment.render())
                print(f"Episode {episode+1}, Step: {steps}, Position: {state['position']}")
                time.sleep(0.1)
            
            # Agent perceives the environment
            agent.perceive(state)
            
            # Agent decides what action to take
            action = agent.decide()
            
            # Agent acts in the environment
            agent.act(action, state)
            
            # Environment updates based on the action
            new_state, reward, done = environment.update(action)
            
            # Agent learns from the experience
            agent.learn(reward, state, action)
            
            # Update state and statistics
            state = new_state
            total_reward += reward
            steps += 1
        
        # Update episode statistics
        episode_rewards.append(total_reward)
        episode_steps.append(steps)
        if done:
            goals_reached += 1
        
        # Print progress
        if (episode + 1) % 10 == 0:
            success_rate = goals_reached / (episode + 1) * 100
            print(f"Episode {episode+1}/{episodes}: "
                  f"Steps={steps}, Reward={total_reward:.2f}, "
                  f"Success Rate={success_rate:.1f}%")
    
    # Calculate final statistics
    success_rate = goals_reached / episodes * 100
    avg_reward = sum(episode_rewards) / episodes
    avg_steps = sum(episode_steps) / episodes
    
    print("\nTraining completed!")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Average Reward: {avg_reward:.2f}")
    print(f"Average Steps: {avg_steps:.1f}")
    
    # Save the trained agent if requested
    if save_path:
        try:
            with open(save_path, 'wb') as f:
                pickle.dump(agent, f)
            print(f"Agent saved to {save_path}")
        except Exception as e:
            print(f"Error saving agent: {e}")
    
    # Return training statistics
    return {
        "agent_type": agent_type,
        "episodes": episodes,
        "success_rate": success_rate,
        "avg_reward": avg_reward,
        "avg_steps": avg_steps,
        "episode_rewards": episode_rewards,
        "episode_steps": episode_steps,
        "agent": agent
    }


def main() -> None:
    """
    Main function to run the training script.
    """
    parser = argparse.ArgumentParser(description="Train an AI agent")
    parser.add_argument("--agent-type", type=str, default="enhanced", 
                        choices=["basic", "enhanced"], help="Type of agent to train")
    parser.add_argument("--episodes", type=int, default=100, help="Number of episodes to train for")
    parser.add_argument("--max-steps", type=int, default=100, help="Maximum steps per episode")
    parser.add_argument("--render", action="store_true", help="Render the environment during training")
    parser.add_argument("--save-path", type=str, default="trained_agent.pkl", 
                        help="Path to save the trained agent")
    parser.add_argument("--no-save", action="store_true", help="Don't save the trained agent")
    parser.add_argument("--plot", action="store_true", help="Plot learning curves after training")
    args = parser.parse_args()
    
    # Train the agent
    save_path = None if args.no_save else args.save_path
    stats = train_agent(
        agent_type=args.agent_type,
        episodes=args.episodes,
        max_steps=args.max_steps,
        render=args.render,
        save_path=save_path
    )
    
    # Plot learning curves if requested
    if args.plot:
        plot_learning_curve(stats["episode_rewards"], stats["episode_steps"])
        
        # If enhanced agent, plot action values
        if args.agent_type.lower() == 'enhanced':
            agent = stats["agent"]
            if hasattr(agent, 'model') and hasattr(agent.model, 'get_all_action_values'):
                # Get action values for a sample state
                sample_state = {
                    "position": (5, 5),
                    "orientation": "right",
                    "goal_position": (9, 9)
                }
                action_values = agent.model.get_all_action_values(sample_state)
                plot_action_values(action_values)


if __name__ == "__main__":
    main()
