"""
Main entry point for running the AI agent.
"""
import argparse
import time
from typing import Dict, Any

from agent import Agent
from environment import Environment


def run_episode(agent: Agent, environment: Environment, max_steps: int = 100, render: bool = True) -> Dict[str, Any]:
    """
    Run a single episode of the agent in the environment.
    
    Args:
        agent: The agent to run
        environment: The environment to run in
        max_steps: Maximum number of steps to run
        render: Whether to render the environment
        
    Returns:
        Dictionary with episode statistics
    """
    # Reset the environment
    state = environment.reset()
    
    total_reward = 0
    steps = 0
    done = False
    
    # Run until done or max steps reached
    while not done and steps < max_steps:
        # Render the environment
        if render:
            print("\n" + environment.render())
            print(f"Step: {steps}, Position: {state['position']}, Orientation: {state['orientation']}")
        
        # Agent perceives the environment
        agent.perceive(state)
        
        # Agent decides what action to take
        action = agent.decide()
        print(f"Agent {agent.name} decides to: {action}")
        
        # Agent acts in the environment
        result, _ = agent.act(action, state)
        print(f"Result: {result}")
        
        # Environment updates based on the action
        new_state, reward, done = environment.update(action)
        
        # Agent learns from the experience
        agent.learn(reward, state, action)
        
        # Update state and statistics
        state = new_state
        total_reward += reward
        steps += 1
        
        # Small delay for visualization
        if render:
            time.sleep(0.5)
    
    # Final render
    if render:
        print("\n" + environment.render())
        print(f"Episode finished after {steps} steps with total reward {total_reward:.2f}")
        if done:
            print("Goal reached!")
        else:
            print("Maximum steps reached without finding the goal.")
    
    # Return episode statistics
    return {
        "steps": steps,
        "total_reward": total_reward,
        "goal_reached": done
    }


def interactive_mode(agent: Agent, environment: Environment) -> None:
    """
    Run the agent in interactive mode, allowing the user to control the agent.
    
    Args:
        agent: The agent to run
        environment: The environment to run in
    """
    state = environment.reset()
    done = False
    steps = 0
    total_reward = 0
    
    print("\nInteractive Mode")
    print("----------------")
    print("Commands:")
    print("  f: move forward")
    print("  b: move backward")
    print("  l: turn left")
    print("  r: turn right")
    print("  w: wait")
    print("  a: let agent decide")
    print("  q: quit")
    
    while not done:
        # Render the environment
        print("\n" + environment.render())
        print(f"Step: {steps}, Position: {state['position']}, Orientation: {state['orientation']}")
        
        # Get user input
        user_input = input("Enter command (f/b/l/r/w/a/q): ").strip().lower()
        
        if user_input == 'q':
            break
        
        # Map user input to action
        action_map = {
            'f': 'move_forward',
            'b': 'move_backward',
            'l': 'turn_left',
            'r': 'turn_right',
            'w': 'wait'
        }
        
        if user_input == 'a':
            # Let agent decide
            agent.perceive(state)
            action = agent.decide()
            print(f"Agent {agent.name} decides to: {action}")
        elif user_input in action_map:
            action = action_map[user_input]
        else:
            print("Invalid command. Try again.")
            continue
        
        # Agent acts in the environment
        result, _ = agent.act(action, state)
        print(f"Result: {result}")
        
        # Environment updates based on the action
        new_state, reward, done = environment.update(action)
        
        # Agent learns from the experience
        agent.learn(reward, state, action)
        
        # Update state and statistics
        state = new_state
        total_reward += reward
        steps += 1
        
        if done:
            print("\n" + environment.render())
            print(f"Goal reached after {steps} steps with total reward {total_reward:.2f}!")


def main() -> None:
    """
    Main function to run the AI agent.
    """
    parser = argparse.ArgumentParser(description="Run a simple AI agent")
    parser.add_argument("--episodes", type=int, default=5, help="Number of episodes to run")
    parser.add_argument("--max-steps", type=int, default=100, help="Maximum steps per episode")
    parser.add_argument("--no-render", action="store_true", help="Disable rendering")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--env-size", type=int, default=10, help="Size of the environment")
    args = parser.parse_args()
    
    # Create agent and environment
    agent = Agent("Explorer")
    environment = Environment(size=(args.env_size, args.env_size))
    
    # Add some rules to the agent
    agent.add_rule("position[0] == 0 and orientation == 'left'", "turn_right")
    agent.add_rule("position[1] == 0 and orientation == 'up'", "turn_right")
    agent.add_rule("position[0] == size[0] - 1 and orientation == 'right'", "turn_left")
    agent.add_rule("position[1] == size[1] - 1 and orientation == 'down'", "turn_left")
    
    if args.interactive:
        # Run in interactive mode
        interactive_mode(agent, environment)
    else:
        # Run episodes
        for episode in range(args.episodes):
            print(f"\n=== Episode {episode + 1}/{args.episodes} ===")
            stats = run_episode(
                agent, 
                environment, 
                max_steps=args.max_steps, 
                render=not args.no_render
            )
            
            # Print episode statistics
            print(f"Episode {episode + 1} statistics:")
            print(f"  Steps: {stats['steps']}")
            print(f"  Total reward: {stats['total_reward']:.2f}")
            print(f"  Goal reached: {stats['goal_reached']}")
    
    # Print final agent status
    print("\nFinal agent status:")
    status = agent.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
