"""
Advanced web interface for the autonomous AI agent.
"""
import os
import pickle
import argparse
import threading
import time
from flask import Flask, render_template, request, jsonify

from agent import Agent
from enhanced_agent import EnhancedAgent
from autonomous_agent import AutonomousAgent
from environment import Environment


app = Flask(__name__)

# Global variables
agent = None
environment = None
current_state = None
episode_history = []
autonomous_thread = None
is_running_autonomously = False


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/api/reset', methods=['POST'])
def reset_environment():
    """Reset the environment and return the initial state."""
    global current_state, episode_history

    # Reset the environment
    current_state = environment.reset()
    episode_history = []

    # Return the initial state
    return jsonify({
        'state': current_state,
        'render': environment.render(),
        'agent_status': agent.get_status()
    })


@app.route('/api/step', methods=['POST'])
def step():
    """Take a step in the environment."""
    global current_state, episode_history

    # Get action from request
    data = request.json
    action = data.get('action')

    if action == 'agent_decide':
        # Let the agent decide
        agent.perceive(current_state)
        action = agent.decide()

    # Execute the action
    result, _ = agent.act(action, current_state)

    # Update the environment
    new_state, reward, done = environment.update(action)

    # Agent learns from the experience
    agent.learn(reward, current_state, action)

    # Update current state
    current_state = new_state

    # Add to episode history
    episode_history.append({
        'action': action,
        'reward': reward,
        'state': current_state.copy()
    })

    # Return the new state
    return jsonify({
        'state': current_state,
        'render': environment.render(),
        'action': action,
        'reward': reward,
        'done': done,
        'result': result,
        'agent_status': agent.get_status(),
        'episode_length': len(episode_history),
        'total_reward': sum(step['reward'] for step in episode_history)
    })


@app.route('/api/agent_info', methods=['GET'])
def agent_info():
    """Get information about the agent."""
    info = {
        'name': agent.name,
        'capabilities': agent.capabilities,
        'memory_size': len(agent.memory),
        'status': agent.get_status(),
        'is_autonomous': is_running_autonomously
    }

    # Add thinking process if available
    if hasattr(agent, 'get_thinking_process'):
        # Only return the last 10 thinking steps to keep the response size manageable
        info['thinking_process'] = agent.get_thinking_process()[-10:]

    return jsonify(info)


@app.route('/api/run_autonomously', methods=['POST'])
def run_autonomously():
    """Start or stop autonomous operation."""
    global autonomous_thread, is_running_autonomously

    data = request.json
    command = data.get('command', 'start')

    if command == 'start' and not is_running_autonomously:
        # Start autonomous operation
        is_running_autonomously = True

        # Define the update callback function
        def update_ui(state, action, reward, done, total_reward):
            global current_state, episode_history
            current_state = state
            episode_history.append({
                'action': action,
                'reward': reward,
                'state': state.copy()
            })

        # Start autonomous operation in a separate thread
        autonomous_thread = threading.Thread(
            target=_run_autonomous_thread,
            args=(update_ui,)
        )
        autonomous_thread.daemon = True
        autonomous_thread.start()

        return jsonify({
            'status': 'started',
            'message': 'Autonomous operation started'
        })

    elif command == 'stop' and is_running_autonomously:
        # Stop autonomous operation
        is_running_autonomously = False

        return jsonify({
            'status': 'stopped',
            'message': 'Autonomous operation stopped'
        })

    else:
        # Invalid command or already in the requested state
        status = 'already_running' if is_running_autonomously else 'not_running'
        return jsonify({
            'status': status,
            'message': f'Agent is already in the requested state: {status}'
        })


@app.route('/api/autonomous_status', methods=['GET'])
def autonomous_status():
    """Get the current status of autonomous operation."""
    return jsonify({
        'is_running': is_running_autonomously,
        'episode_length': len(episode_history),
        'total_reward': sum(step['reward'] for step in episode_history) if episode_history else 0
    })


def _run_autonomous_thread(update_callback):
    """Run the autonomous agent in a separate thread."""
    global is_running_autonomously, current_state

    # If the agent has run_autonomously method, use it
    if hasattr(agent, 'run_autonomously'):
        agent.run_autonomously(environment, update_callback)
    else:
        # Otherwise, implement autonomous operation here
        max_steps = 200
        step_count = 0

        while is_running_autonomously and step_count < max_steps:
            # Check if we're done
            if current_state.get('done', False):
                break

            # Let the agent decide
            agent.perceive(current_state)
            action = agent.decide()

            # Execute the action
            result, _ = agent.act(action, current_state)

            # Update the environment
            new_state, reward, done = environment.update(action)

            # Agent learns from the experience
            agent.learn(reward, current_state, action)

            # Update current state
            current_state = new_state

            # Call the update callback
            update_callback(current_state, action, reward, done,
                           sum(step['reward'] for step in episode_history))

            # Increment step count
            step_count += 1

            # Small delay for visualization
            time.sleep(0.5)

    # Mark as no longer running
    is_running_autonomously = False


def create_app(agent_path=None, agent_type='autonomous', env_size=10):
    """Create and configure the Flask app."""
    global agent, environment, current_state

    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)

    # Create the HTML template
    with open('templates/index.html', 'w') as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous AI Agent Interface</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .container {
            display: flex;
            flex-wrap: wrap;
        }
        .environment {
            flex: 1;
            min-width: 400px;
            border: 1px solid #ccc;
            padding: 20px;
            margin-right: 20px;
            margin-bottom: 20px;
        }
        .controls {
            flex: 1;
            min-width: 400px;
            border: 1px solid #ccc;
            padding: 20px;
            margin-bottom: 20px;
        }
        .status {
            flex: 1;
            min-width: 400px;
            border: 1px solid #ccc;
            padding: 20px;
        }
        .thinking {
            flex: 1;
            min-width: 400px;
            border: 1px solid #ccc;
            padding: 20px;
            margin-top: 20px;
        }
        pre {
            background-color: #f5f5f5;
            padding: 10px;
            overflow: auto;
            white-space: pre-wrap;
        }
        button {
            padding: 8px 16px;
            margin: 5px;
            cursor: pointer;
        }
        .action-buttons {
            display: flex;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }
        .autonomous-buttons {
            display: flex;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        .episode-info {
            margin-top: 20px;
        }
        .autonomous-button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 4px;
        }
        .stop-button {
            background-color: #f44336;
        }
        .thinking-process {
            margin-top: 20px;
            border-top: 1px solid #ccc;
            padding-top: 10px;
        }
        .thinking-step {
            margin-bottom: 10px;
            padding: 5px;
            border-left: 3px solid #4CAF50;
            padding-left: 10px;
        }
        .status-running {
            color: green;
            font-weight: bold;
        }
        .status-stopped {
            color: red;
        }
    </style>
</head>
<body>
    <h1>Autonomous AI Agent Interface</h1>

    <div class="container">
        <div class="environment">
            <h2>Environment</h2>
            <pre id="environment-render"></pre>
        </div>

        <div class="controls">
            <h2>Controls</h2>
            <button id="reset-button">Reset Environment</button>

            <div class="autonomous-buttons">
                <button id="run-autonomous-button" class="autonomous-button">Run Autonomously</button>
                <button id="stop-autonomous-button" class="autonomous-button stop-button">Stop</button>
            </div>

            <h3>Manual Actions</h3>
            <div class="action-buttons">
                <button class="action-button" data-action="move_forward">Move Forward</button>
                <button class="action-button" data-action="move_backward">Move Backward</button>
                <button class="action-button" data-action="turn_left">Turn Left</button>
                <button class="action-button" data-action="turn_right">Turn Right</button>
                <button class="action-button" data-action="wait">Wait</button>
                <button class="action-button" data-action="agent_decide">Single Step</button>
            </div>

            <div class="episode-info">
                <h3>Episode Information</h3>
                <p>Autonomous Mode: <span id="autonomous-status" class="status-stopped">Not Running</span></p>
                <p>Steps: <span id="episode-length">0</span></p>
                <p>Total Reward: <span id="total-reward">0.0</span></p>
                <p>Last Action: <span id="last-action">None</span></p>
                <p>Last Reward: <span id="last-reward">0.0</span></p>
                <p>Done: <span id="done-status">False</span></p>
            </div>
        </div>

        <div class="status">
            <h2>Agent Status</h2>
            <pre id="agent-status"></pre>
        </div>

        <div class="thinking">
            <h2>Agent Thinking Process</h2>
            <div id="thinking-process" class="thinking-process">
                <p>The agent's thought process will appear here when running autonomously.</p>
            </div>
        </div>
    </div>

    <script>
        // Global variables
        let isAutonomous = false;
        let statusCheckInterval = null;

        // Initialize the environment
        function resetEnvironment() {
            fetch('/api/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('environment-render').textContent = data.render;
                document.getElementById('agent-status').textContent = JSON.stringify(data.agent_status, null, 2);
                document.getElementById('episode-length').textContent = '0';
                document.getElementById('total-reward').textContent = '0.0';
                document.getElementById('last-action').textContent = 'None';
                document.getElementById('last-reward').textContent = '0.0';
                document.getElementById('done-status').textContent = 'False';

                // Enable all action buttons
                document.querySelectorAll('.action-button').forEach(button => {
                    button.disabled = false;
                });
            });
        }

        // Take a step in the environment
        function takeStep(action) {
            fetch('/api/step', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ action: action })
            })
            .then(response => response.json())
            .then(data => {
                updateUI(data);
            });
        }

        // Update the UI with new data
        function updateUI(data) {
            document.getElementById('environment-render').textContent = data.render;
            document.getElementById('agent-status').textContent = JSON.stringify(data.agent_status, null, 2);
            document.getElementById('episode-length').textContent = data.episode_length;
            document.getElementById('total-reward').textContent = data.total_reward.toFixed(2);
            document.getElementById('last-action').textContent = data.action;
            document.getElementById('last-reward').textContent = data.reward.toFixed(2);
            document.getElementById('done-status').textContent = data.done;

            // Disable action buttons if done
            if (data.done) {
                document.querySelectorAll('.action-button').forEach(button => {
                    button.disabled = true;
                });

                // Also stop autonomous mode if running
                if (isAutonomous) {
                    stopAutonomous();
                }
            }

            // Update thinking process
            updateThinkingProcess();
        }

        // Start autonomous operation
        function startAutonomous() {
            fetch('/api/run_autonomously', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ command: 'start' })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'started') {
                    isAutonomous = true;
                    document.getElementById('autonomous-status').textContent = 'Running';
                    document.getElementById('autonomous-status').className = 'status-running';

                    // Disable manual action buttons during autonomous operation
                    document.querySelectorAll('.action-button').forEach(button => {
                        button.disabled = true;
                    });

                    // Start polling for status updates
                    statusCheckInterval = setInterval(checkAutonomousStatus, 500);
                }
            });
        }

        // Stop autonomous operation
        function stopAutonomous() {
            fetch('/api/run_autonomously', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ command: 'stop' })
            })
            .then(response => response.json())
            .then(data => {
                isAutonomous = false;
                document.getElementById('autonomous-status').textContent = 'Stopped';
                document.getElementById('autonomous-status').className = 'status-stopped';

                // Enable manual action buttons
                if (document.getElementById('done-status').textContent !== 'true') {
                    document.querySelectorAll('.action-button').forEach(button => {
                        button.disabled = false;
                    });
                }

                // Stop polling for status updates
                if (statusCheckInterval) {
                    clearInterval(statusCheckInterval);
                    statusCheckInterval = null;
                }
            });
        }

        // Check the status of autonomous operation
        function checkAutonomousStatus() {
            fetch('/api/autonomous_status')
                .then(response => response.json())
                .then(data => {
                    if (!data.is_running) {
                        // Autonomous operation has stopped
                        stopAutonomous();
                    } else {
                        // Update episode information
                        document.getElementById('episode-length').textContent = data.episode_length;
                        document.getElementById('total-reward').textContent = data.total_reward.toFixed(2);

                        // Update environment render and agent status
                        fetch('/api/step', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ action: 'wait' })
                        })
                        .then(response => response.json())
                        .then(stepData => {
                            document.getElementById('environment-render').textContent = stepData.render;
                            document.getElementById('agent-status').textContent = JSON.stringify(stepData.agent_status, null, 2);
                            document.getElementById('last-action').textContent = stepData.action;
                            document.getElementById('last-reward').textContent = stepData.reward.toFixed(2);
                            document.getElementById('done-status').textContent = stepData.done;

                            // Update thinking process
                            updateThinkingProcess();
                        });
                    }
                });
        }

        // Update the thinking process display
        function updateThinkingProcess() {
            fetch('/api/agent_info')
                .then(response => response.json())
                .then(data => {
                    if (data.thinking_process) {
                        const thinkingDiv = document.getElementById('thinking-process');
                        thinkingDiv.innerHTML = '';

                        data.thinking_process.forEach(step => {
                            const stepDiv = document.createElement('div');
                            stepDiv.className = 'thinking-step';

                            // Format the thinking step based on its type
                            let content = '';
                            if (step.type === 'perception') {
                                content = `<strong>Perceiving:</strong> Position ${step.position}, Orientation ${step.orientation}`;
                            } else if (step.type === 'decision') {
                                content = `<strong>Deciding:</strong> Action ${step.action} (Plan steps remaining: ${step.remaining_plan_steps})`;
                            } else if (step.type === 'planning') {
                                content = `<strong>Planning:</strong> ${step.result}`;
                                if (step.plan_length) {
                                    content += ` - Created plan with ${step.plan_length} steps`;
                                }
                            }

                            stepDiv.innerHTML = content;
                            thinkingDiv.appendChild(stepDiv);
                        });
                    }
                });
        }

        // Add event listeners
        document.getElementById('reset-button').addEventListener('click', resetEnvironment);

        document.getElementById('run-autonomous-button').addEventListener('click', startAutonomous);
        document.getElementById('stop-autonomous-button').addEventListener('click', stopAutonomous);

        document.querySelectorAll('.action-button').forEach(button => {
            button.addEventListener('click', function() {
                const action = this.getAttribute('data-action');
                takeStep(action);
            });
        });

        // Initialize on page load
        window.addEventListener('load', resetEnvironment);
    </script>
</body>
</html>""")

    # Load or create agent
    if agent_path and os.path.exists(agent_path):
        try:
            with open(agent_path, 'rb') as f:
                agent = pickle.load(f)
            print(f"Loaded agent from {agent_path}")
        except Exception as e:
            print(f"Error loading agent: {e}")
            agent = None

    if agent is None:
        # Create a new agent
        if agent_type.lower() == 'autonomous':
            agent = AutonomousAgent("AutonomousAgent")
        elif agent_type.lower() == 'enhanced':
            agent = EnhancedAgent("WebAgent")
        else:
            agent = Agent("WebAgent")
        print(f"Created new {agent_type} agent")

    # Create environment
    environment = Environment(size=(env_size, env_size))

    # Initialize current state
    current_state = environment.reset()

    return app


def main():
    """Main function to run the web interface."""
    parser = argparse.ArgumentParser(description="Run the AI agent web interface")
    parser.add_argument("--agent-path", type=str, help="Path to a saved agent")
    parser.add_argument("--agent-type", type=str, default="autonomous",
                        choices=["basic", "enhanced", "autonomous"],
                        help="Type of agent to create if none is loaded")
    parser.add_argument("--env-size", type=int, default=10, help="Size of the environment")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on")
    args = parser.parse_args()

    app = create_app(args.agent_path, args.agent_type, args.env_size)
    app.run(debug=True, port=args.port)


if __name__ == "__main__":
    main()
