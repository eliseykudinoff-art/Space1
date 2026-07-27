"""
External Market Environment Model (G3)

Provides models for representing the external marketplace:
- MarketLead: A job listing containing price, estimated time, and requirements
- ClientProfile: Defines client behavior, rigor, budget capacities, and feedback multipliers
- MarketEnvironment: Simulates streaming task flows, client reviews, and competitive pressure
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import random
from datetime import datetime

from ..models.task import Task, create_task, TaskPriority


@dataclass
class ClientProfile:
    """Client Profile determining review habits and pay rate limits."""
    id: str
    name: str
    rigor: float = 0.5  # Higher means harder to satisfy quality (lower review scores)
    max_budget: float = 500.0
    reputation_multiplier: float = 1.0  # multiplier to upsilon reviews
    is_demanding: bool = False


@dataclass
class MarketLead:
    """A raw lead available on the freelance platform."""
    id: str
    title: str
    client: ClientProfile
    budget: float
    required_quality: float = 0.7
    estimated_hours: float = 2.0
    urgency: float = 0.5


class MarketEnvironment:
    """
    MarketEnvironment (G3).
    
    Simulates the external freelancing ecosystem:
    - Streams candidate task leads.
    - Simulates competitive bids (competitors snatching low-bid/high-cost tasks).
    - Client feedback multipliers.
    """
    
    def __init__(self):
        self._available_leads: List[MarketLead] = []
        self._competitor_pressure: float = 0.3  # [0.0, 1.0] chance competitor claims a lead
        
    def add_lead(self, lead: MarketLead) -> None:
        """Register a new lead in the stream."""
        self._available_leads.append(lead)
        
    def stream_leads(self, count: int = 5) -> List[Task]:
        """
        Generate and stream available Tasks representing leads in the marketplace.
        
        Args:
            count: Number of tasks to generate
            
        Returns:
            List of Task instances
        """
        tasks = []
        clients = [
            ClientProfile("c-1", "AlphaCorp", rigor=0.3, max_budget=1000.0, reputation_multiplier=1.2),
            ClientProfile("c-2", "BetaInc", rigor=0.8, max_budget=200.0, is_demanding=True),
            ClientProfile("c-3", "GammaLtd", rigor=0.5, max_budget=500.0),
        ]
        
        # Pull from pre-existing leads or generate randomized ones
        for i in range(count):
            if self._available_leads:
                lead = self._available_leads.pop(0)
            else:
                client = random.choice(clients)
                lead = MarketLead(
                    id=f"lead_{i}_{int(datetime.now().timestamp())}",
                    title=f"Freelance task for {client.name}",
                    client=client,
                    budget=random.uniform(20.0, client.max_budget),
                    required_quality=random.uniform(0.5, 0.9 if client.is_demanding else 0.8),
                    estimated_hours=random.uniform(1.0, 8.0)
                )
                
            # Convert lead to Task object with G3 context metadata
            task = create_task(
                title=lead.title,
                priority=TaskPriority.HIGH if lead.urgency > 0.7 else TaskPriority.MEDIUM,
                estimated_hours=lead.estimated_hours
            )
            task.revenue = lead.budget
            task.metadata.update({
                "client_id": lead.client.id,
                "client_rigor": lead.client.rigor,
                "client_reputation_multiplier": lead.client.reputation_multiplier,
                "quality_requirement": lead.required_quality,
                "lead_id": lead.id
            })
            tasks.append(task)
            
        return tasks
        
    def simulate_competition(self, task: Task) -> bool:
        """
        Simulate competitor bidding pressure.
        
        Returns:
            True if competitor wins the task, False if agent gets the task.
        """
        # If task has very high margins (high budget, low estimated time), competitors bid more aggressively
        revenue = getattr(task, "revenue", None) or 0.0
        time_spent = getattr(task, "estimated_hours", 1.0)
        margin = revenue / max(time_spent, 1e-9)
        
        adjusted_pressure = self._competitor_pressure
        if margin > 100.0:
            adjusted_pressure += 0.3
            
        # Draw random outcome
        return random.random() < adjusted_pressure
        
    def generate_review(self, task: Task, achieved_quality: float) -> Dict[str, Any]:
        """
        Generate feedback and rating review score based on client profile rigor.
        
        Args:
            task: Completed Task
            achieved_quality: Quality score achieved
            
        Returns:
            Dict containing rating, feedback message, and reputation score multiplier.
        """
        rigor = task.metadata.get("client_rigor", 0.5)
        req_quality = task.metadata.get("quality_requirement", 0.7)
        multiplier = task.metadata.get("client_reputation_multiplier", 1.0)
        
        quality_delta = achieved_quality - req_quality
        
        # Map quality difference and rigor to 1.0-5.0 rating score
        if quality_delta >= 0.1:
            rating = 5.0
            feedback = "Excellent output! Exceeded our requirements."
        elif quality_delta >= 0.0:
            rating = 4.0 + (quality_delta * 10)
            rating = min(5.0, rating)
            feedback = "Satisfactory job."
        else:
            # Below requirements
            rating = 3.0 - (abs(quality_delta) * 10) * rigor
            rating = max(1.0, rating)
            feedback = "Did not satisfy requirements. Poor quality."
            
        return {
            "rating": rating,
            "feedback": feedback,
            "reputation_multiplier": multiplier,
        }
