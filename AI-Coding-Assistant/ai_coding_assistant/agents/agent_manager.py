"""
Agent manager for the AI Coding Assistant.

This module manages the autonomous agent system.
"""

import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from ai_coding_assistant.core.config import Config
from ai_coding_assistant.models.model_manager import ModelManager
from ai_coding_assistant.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class AgentManager:
    """Manager for autonomous agents."""

    def __init__(
        self, config: Config, model_manager: ModelManager, tool_registry: ToolRegistry
    ) -> None:
        """Initialize the agent manager with configuration."""
        self.config = config
        self.model_manager = model_manager
        self.tool_registry = tool_registry
        self.tasks: Dict[str, Dict[str, Any]] = {}
        logger.info("Initialized agent manager")

    async def process_task(
        self,
        task: str,
        context_items: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        conversation_id: str,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Process a task using the agent system.

        Args:
            task: The task to process
            context_items: Context items for the task
            tools: Available tools
            conversation_id: ID of the conversation

        Returns:
            A tuple of (response_text, tool_calls)
        """
        # Create a task ID
        task_id = str(uuid.uuid4())

        # Create a task record
        self.tasks[task_id] = {
            "id": task_id,
            "conversation_id": conversation_id,
            "task": task,
            "status": "planning",
            "steps": [],
            "current_step": 0,
            "result": None,
        }

        try:
            # Generate a plan
            plan = await self._generate_plan(task, context_items)

            # Update task record
            self.tasks[task_id]["plan"] = plan
            self.tasks[task_id]["status"] = "executing"

            # Execute the plan
            result, tool_calls = await self._execute_plan(
                task_id, plan, context_items, tools
            )

            # Update task record
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["result"] = result

            return result, tool_calls

        except Exception as e:
            logger.exception(f"Error processing task: {e}")

            # Update task record
            self.tasks[task_id]["status"] = "failed"
            self.tasks[task_id]["error"] = str(e)

            # Return error message
            return f"Error processing task: {str(e)}", []

    async def _generate_plan(
        self, task: str, context_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate a plan for a task.

        Args:
            task: The task to generate a plan for
            context_items: Context items for the task

        Returns:
            A list of plan steps
        """
        # Create a planning prompt
        planning_prompt = (
            f"Task: {task}\n\n"
            "Generate a step-by-step plan to complete this task. "
            "Each step should be a specific action that can be executed. "
            "For each step, provide:\n"
            "1. A description of the action\n"
            "2. Any tools needed for the action\n"
            "3. Expected outcome of the action\n\n"
            "Format your response as a JSON array of steps, where each step has "
            "'description', 'tools', and 'expected_outcome' fields."
        )

        # Generate a plan
        system_prompt = (
            "You are an AI coding assistant that helps with programming tasks. "
            "You are generating a plan to complete a task. "
            "Be specific, detailed, and comprehensive in your planning."
        )

        # Generate the plan
        plan_text, _ = await self.model_manager.generate_response(
            planning_prompt, context_items
        )

        # Parse the plan
        try:
            # Extract JSON from the response
            json_match = re.search(r'```json\n(.*?)\n```', plan_text, re.DOTALL)
            if json_match:
                plan_json = json_match.group(1)
            else:
                # Try to find JSON array directly
                json_match = re.search(r'\[\s*{.*}\s*\]', plan_text, re.DOTALL)
                if json_match:
                    plan_json = json_match.group(0)
                else:
                    # Assume the entire response is JSON
                    plan_json = plan_text

            # Parse the JSON
            plan = json.loads(plan_json)

            # Validate the plan
            if not isinstance(plan, list):
                raise ValueError("Plan must be a list of steps")

            for step in plan:
                if not isinstance(step, dict):
                    raise ValueError("Each step must be a dictionary")

                if "description" not in step:
                    raise ValueError("Each step must have a description")

            return plan

        except Exception as e:
            logger.exception(f"Error parsing plan: {e}")

            # Create a simple plan as fallback
            return [
                {
                    "description": f"Complete the task: {task}",
                    "tools": [],
                    "expected_outcome": "Task completed successfully",
                }
            ]

    async def _execute_plan(
        self,
        task_id: str,
        plan: List[Dict[str, Any]],
        context_items: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Execute a plan.

        Args:
            task_id: ID of the task
            plan: The plan to execute
            context_items: Context items for the task
            tools: Available tools

        Returns:
            A tuple of (response_text, tool_calls)
        """
        # Initialize variables
        all_tool_calls = []
        step_results = []

        # Execute each step in the plan
        for i, step in enumerate(plan):
            # Update task record
            self.tasks[task_id]["current_step"] = i

            # Create step prompt
            step_prompt = (
                f"Task: {self.tasks[task_id]['task']}\n\n"
                f"Current step ({i+1}/{len(plan)}): {step['description']}\n\n"
            )

            # Add previous step results
            if step_results:
                step_prompt += "Previous step results:\n"
                for j, result in enumerate(step_results):
                    step_prompt += f"Step {j+1}: {result}\n"
                step_prompt += "\n"

            step_prompt += (
                "Execute this step and provide a detailed response. "
                "Use the available tools if needed."
            )

            # Execute the step
            step_response, step_tool_calls = await self.model_manager.generate_response(
                step_prompt, context_items, tools
            )

            # Record tool calls
            all_tool_calls.extend(step_tool_calls)

            # Record step result
            step_results.append(step_response)

            # Update task record
            self.tasks[task_id]["steps"].append({
                "description": step["description"],
                "response": step_response,
                "tool_calls": step_tool_calls,
            })

        # Generate final response
        final_prompt = (
            f"Task: {self.tasks[task_id]['task']}\n\n"
            "You have completed all steps in the plan. "
            "Provide a summary of what you did and the results."
        )

        # Add step results
        final_prompt += "\n\nStep results:\n"
        for i, result in enumerate(step_results):
            final_prompt += f"Step {i+1}: {result}\n"

        # Generate final response
        final_response, _ = await self.model_manager.generate_response(
            final_prompt, context_items
        )

        return final_response, all_tool_calls
