#!/usr/bin/env python3
"""
Multi-Agent Workflow Demo for Space1
=====================================
Demonstrates how to use the multi-agent system with OpenHands SDK.

Usage:
    python multi_agent_demo.py
"""

import os
import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

# Check if OpenHands SDK is available
SDK_AVAILABLE = False
try:
    from openhands.sdk import LLM, Agent, Conversation
    from openhands.sdk.context import AgentContext
    from openhands.sdk.subagent import register_agent
    from openhands.tools.task import TaskToolSet
    from openhands.tools.file_editor import FileEditorTool
    from openhands.tools.terminal import TerminalTool
    SDK_AVAILABLE = True
except ImportError:
    print("⚠️  OpenHands SDK not installed. Install with: pip install openhands-sdk")
    print("   Showing workflow structure only.\n")


def load_agent(name: str) -> str:
    """Load agent definition from .agents directory."""
    agent_path = Path(__file__).parent / ".agents" / f"{name}.md"
    if agent_path.exists():
        return agent_path.read_text()
    return ""


def create_agent(name: str, llm=None):
    """Create an agent from the .agents directory."""
    if not SDK_AVAILABLE or llm is None:
        return None
        
    agent_content = load_agent(name)
    
    skills = []
    if agent_content:
        skills.append(
            type("Skill", (), {
                "name": f"{name}_agent",
                "content": agent_content,
                "trigger": None
            })()
        )
    
    return Agent(
        llm=llm,
        tools=[],
        agent_context=AgentContext(
            skills=skills,
            system_message_suffix=f"You are the {name} agent."
        )
    )


async def demo_workflow():
    """Demonstrate the multi-agent workflow."""
    print("=" * 70)
    print("MULTI-AGENT WORKFLOW DEMO - Space1")
    print("=" * 70)
    
    # Step 1: Show available agents
    print("\n📋 AVAILABLE AGENTS:")
    print("-" * 40)
    agents_dir = Path(__file__).parent / ".agents"
    for agent_file in sorted(agents_dir.glob("*.md")):
        name = agent_file.stem
        content = agent_file.read_text()
        # Extract description from frontmatter
        desc = ""
        for line in content.split("\n"):
            if line.startswith("description:"):
                desc = line.replace("description:", "").strip()
                break
        print(f"  • {name:15} - {desc}")
    
    # Step 2: Show workflow structure
    print("\n🔄 WORKFLOW STRUCTURE:")
    print("-" * 40)
    print("""
    User Request
         │
         ▼
    ┌─────────────┐
    │  COORDINATOR│ ← Orchestrates the workflow
    └──────┬──────┘
           │
    ┌──────┼──────┐
    ▼      ▼      ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ARCHITECT│ │DEVELOPER│ │ REVIEWER│
└─────────┘ └─────────┘ └─────────┘
    Design    Implement   Validate
""")
    
    # Step 3: Show SDK usage if available
    if SDK_AVAILABLE:
        print("🔧 SDK INTEGRATION:")
        print("-" * 40)
        print("""
from openhands.sdk import LLM, Agent, Conversation

# Configure LLM
llm = LLM(
    model="gpt-5",
    api_key=os.getenv("OPENAI_API_KEY")
)

# Create agents
architect = create_agent("architect", llm)
developer = create_agent("developer", llm)
reviewer = create_agent("reviewer", llm)

# Run workflow
conversation = Conversation(
    agent=architect,
    workspace=os.getcwd()
)
conversation.send_message("Design a new feature for...")
conversation.run()
""")
        
        # Try to initialize if API key is available
        if os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY"):
            print("\n🚀 TESTING SDK CONNECTION...")
            try:
                llm = LLM(
                    model=os.getenv("LLM_MODEL", "gpt-5"),
                    api_key=os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
                    base_url=os.environ.get("LLM_BASE_URL", None)
                )
                test_conversation = Conversation(
                    agent=create_agent("architect", llm) or Agent(llm=llm, tools=[]),
                    workspace=os.getcwd()
                )
                test_conversation.send_message("Say 'Hello from multi-agent system!' and stop.")
                test_conversation.run()
                print("✅ SDK connection successful!")
            except Exception as e:
                print(f"⚠️  SDK test failed: {e}")
        else:
            print("\n⚠️  No LLM API key found. Set OPENAI_API_KEY or LLM_API_KEY to test.")
    else:
        print("\n📦 To enable full SDK integration:")
        print("   pip install openhands-sdk openhands-tools")
    
    # Step 4: Example workflow
    print("\n📝 EXAMPLE WORKFLOW:")
    print("-" * 40)
    print("""
Task: "Add user authentication to the API"

Step 1 - COORDINATOR:
  → Analyzes task complexity (MEDIUM)
  → Decides: ARCHITECT → DEVELOPER → REVIEWER

Step 2 - ARCHITECT:
  → Designs auth module structure
  → Defines API endpoints
  → Specifies database schema

Step 3 - DEVELOPER:
  → Implements auth.py module
  → Adds JWT handling
  → Writes unit tests

Step 4 - REVIEWER:
  → Checks code quality
  → Validates security
  → Suggests improvements

Result: Merged authentication feature ready for production!
""")


def main():
    """Main entry point."""
    print("\n🧠 MULTI-AGENT SYSTEM FOR SPACE1")
    print("   Version 1.0.0\n")
    
    # Run async demo
    asyncio.run(demo_workflow())
    
    print("\n" + "=" * 70)
    print("For more information, see .agents/ directory and PROJECT_NOTE.md")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()