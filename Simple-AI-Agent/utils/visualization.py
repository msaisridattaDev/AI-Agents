"""
Visualization utilities for the AI agent.
"""
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple, Any


def plot_environment(environment_state: Dict[str, Any], figsize: Tuple[int, int] = (8, 8)) -> None:
    """
    Plot the environment state.
    
    Args:
        environment_state: The environment state to plot
        figsize: Figure size
    """
    # Extract information from the environment state
    position = environment_state.get("position", (0, 0))
    orientation = environment_state.get("orientation", "right")
    obstacles = environment_state.get("obstacles", [])
    goal_position = environment_state.get("goal_position", (9, 9))
    size = environment_state.get("size", (10, 10))
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Set limits
    ax.set_xlim(-0.5, size[0] - 0.5)
    ax.set_ylim(-0.5, size[1] - 0.5)
    
    # Draw grid
    for i in range(size[0] + 1):
        ax.axvline(i - 0.5, color='gray', linestyle='-', alpha=0.5)
    for i in range(size[1] + 1):
        ax.axhline(i - 0.5, color='gray', linestyle='-', alpha=0.5)
    
    # Draw obstacles
    for obs in obstacles:
        ax.add_patch(plt.Rectangle((obs[0] - 0.5, obs[1] - 0.5), 1, 1, color='black'))
    
    # Draw goal
    ax.add_patch(plt.Rectangle((goal_position[0] - 0.5, goal_position[1] - 0.5), 1, 1, color='green', alpha=0.5))
    ax.text(goal_position[0], goal_position[1], 'G', ha='center', va='center', color='black', fontsize=14)
    
    # Draw agent
    ax.add_patch(plt.Circle((position[0], position[1]), 0.3, color='blue'))
    
    # Draw orientation arrow
    arrow_length = 0.4
    dx, dy = 0, 0
    if orientation == "right":
        dx = arrow_length
    elif orientation == "left":
        dx = -arrow_length
    elif orientation == "up":
        dy = arrow_length
    elif orientation == "down":
        dy = -arrow_length
    
    ax.arrow(position[0], position[1], dx, dy, head_width=0.2, head_length=0.2, fc='white', ec='white')
    
    # Set labels and title
    ax.set_xticks(range(size[0]))
    ax.set_yticks(range(size[1]))
    ax.set_title(f"Environment State\nPosition: {position}, Orientation: {orientation}")
    
    # Show the plot
    plt.tight_layout()
    plt.show()


def plot_learning_curve(episode_rewards: List[float], episode_steps: List[int], window_size: int = 10) -> None:
    """
    Plot learning curves for the agent.
    
    Args:
        episode_rewards: List of total rewards for each episode
        episode_steps: List of steps taken for each episode
        window_size: Window size for moving average
    """
    # Create figure and axes
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # Plot rewards
    episodes = range(1, len(episode_rewards) + 1)
    ax1.plot(episodes, episode_rewards, 'b-', alpha=0.3)
    
    # Plot moving average of rewards
    if len(episode_rewards) >= window_size:
        moving_avg = [np.mean(episode_rewards[max(0, i - window_size):i]) 
                     for i in range(1, len(episode_rewards) + 1)]
        ax1.plot(episodes, moving_avg, 'r-')
    
    ax1.set_xlabel('Episode')
    ax1.set_ylabel('Total Reward')
    ax1.set_title('Episode Rewards')
    ax1.grid(True)
    
    # Plot steps
    ax2.plot(episodes, episode_steps, 'g-', alpha=0.3)
    
    # Plot moving average of steps
    if len(episode_steps) >= window_size:
        moving_avg = [np.mean(episode_steps[max(0, i - window_size):i]) 
                     for i in range(1, len(episode_steps) + 1)]
        ax2.plot(episodes, moving_avg, 'r-')
    
    ax2.set_xlabel('Episode')
    ax2.set_ylabel('Steps')
    ax2.set_title('Episode Steps')
    ax2.grid(True)
    
    plt.tight_layout()
    plt.show()


def plot_action_values(action_values: Dict[str, float], top_n: int = 10) -> None:
    """
    Plot the top action values learned by the agent.
    
    Args:
        action_values: Dictionary of action values
        top_n: Number of top values to show
    """
    # Sort action values
    sorted_values = sorted(action_values.items(), key=lambda x: x[1], reverse=True)
    
    # Take top N
    top_values = sorted_values[:top_n]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot bars
    actions = [item[0] for item in top_values]
    values = [item[1] for item in top_values]
    
    ax.barh(range(len(actions)), values, align='center')
    ax.set_yticks(range(len(actions)))
    ax.set_yticklabels(actions)
    ax.invert_yaxis()  # Labels read top-to-bottom
    
    ax.set_xlabel('Value')
    ax.set_title('Top Action Values')
    
    plt.tight_layout()
    plt.show()


def visualize_agent_memory(memory: List[Tuple[str, Any]], last_n: int = 20) -> None:
    """
    Visualize the agent's memory.
    
    Args:
        memory: List of memory entries (type, data)
        last_n: Number of recent memory entries to show
    """
    # Take the last N entries
    recent_memory = memory[-last_n:] if len(memory) > last_n else memory
    
    # Count entry types
    entry_types = {}
    for entry_type, _ in recent_memory:
        entry_types[entry_type] = entry_types.get(entry_type, 0) + 1
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    # Plot memory timeline
    types = [entry[0] for entry in recent_memory]
    unique_types = list(set(types))
    type_indices = {t: i for i, t in enumerate(unique_types)}
    
    # Plot memory entries as a timeline
    for i, (entry_type, _) in enumerate(recent_memory):
        ax1.scatter(i, type_indices[entry_type], marker='o', 
                   c={'perception': 'blue', 'decision': 'green', 
                      'action': 'red', 'learning': 'purple'}.get(entry_type, 'gray'))
    
    ax1.set_xticks(range(len(recent_memory)))
    ax1.set_yticks(range(len(unique_types)))
    ax1.set_yticklabels(unique_types)
    ax1.set_xlabel('Memory Index')
    ax1.set_ylabel('Entry Type')
    ax1.set_title('Agent Memory Timeline')
    
    # Plot entry type distribution
    ax2.pie(entry_types.values(), labels=entry_types.keys(), autopct='%1.1f%%',
           colors=['blue', 'green', 'red', 'purple'])
    ax2.set_title('Memory Entry Types')
    
    plt.tight_layout()
    plt.show()
