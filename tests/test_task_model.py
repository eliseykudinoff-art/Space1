"""
Tests for Task Model with Deadline Awareness

Reference: DEVELOPMENT_PLAN.md - G23
"""

import pytest
from datetime import datetime, timedelta, time as dt_time

from space1.models import (
    Task,
    TaskStatus,
    TaskPriority,
    create_task,
    calculate_schedule,
)


class TestTask:
    """Test Task model with deadline awareness."""
    
    def test_create_task_no_deadline(self):
        """Test creating task without deadline."""
        task = create_task(
            title="No deadline task",
            priority=TaskPriority.MEDIUM,
        )
        
        assert task.title == "No deadline task"
        assert task.deadline is None
        assert task.status == TaskStatus.PENDING
        assert task.urgency_score == 0.5  # Default
        assert task.slack_time == 24.0  # Default
    
    def test_create_task_with_deadline(self):
        """Test creating task with deadline."""
        deadline = datetime.now() + timedelta(hours=4)
        task = create_task(
            title="Urgent task",
            deadline=deadline,
            priority=TaskPriority.HIGH,
        )
        
        assert task.deadline is not None
        assert task.status == TaskStatus.PENDING
        # Slack time should be ~4 hours
        assert 3.5 < task.slack_time < 4.5
        # Urgency should be higher than default
        assert task.urgency_score > 0.5
    
    def test_urgency_calculation_far_deadline(self):
        """Test urgency for far future deadline."""
        deadline = datetime.now() + timedelta(hours=48)
        task = create_task(title="Far deadline", deadline=deadline)
        
        # Far deadline = low urgency
        assert task.urgency_score < 0.5
        assert task.slack_time > 40  # ~48 hours
    
    def test_urgency_calculation_near_deadline(self):
        """Test urgency for near deadline."""
        deadline = datetime.now() + timedelta(hours=1)
        task = create_task(title="Near deadline", deadline=deadline)
        
        # Near deadline = high urgency
        assert task.urgency_score > 0.7
        assert task.slack_time < 2  # ~1 hour
    
    def test_overdue_task(self):
        """Test overdue detection."""
        deadline = datetime.now() - timedelta(hours=1)
        task = create_task(title="Overdue", deadline=deadline)
        
        assert task.is_overdue == True
        assert task.urgency_score == 1.0  # Max urgency
        assert task.slack_time == 0.0
    
    def test_critical_task(self):
        """Test critical task detection."""
        deadline = datetime.now() + timedelta(minutes=30)
        task = create_task(title="Critical", deadline=deadline)
        
        assert task.is_critical == True
        assert task.urgency_score > 0.8
    
    def test_task_start(self):
        """Test starting a task."""
        task = create_task(title="Test task")
        
        assert task.can_start == True
        result = task.start()
        
        assert result == True
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None
    
    def test_task_complete(self):
        """Test completing a task."""
        task = create_task(title="Test task")
        task.start()
        
        result = task.complete()
        
        assert result == True
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
    
    def test_task_fail(self):
        """Test failing a task."""
        task = create_task(title="Test task")
        task.start()
        
        task.fail(reason="Network error")
        
        assert task.status == TaskStatus.FAILED
        assert task.metadata["failure_reason"] == "Network error"
    
    def test_refresh_deadline(self):
        """Test refreshing deadline fields."""
        deadline = datetime.now() + timedelta(hours=2)
        task = create_task(title="Test", deadline=deadline)
        
        original_slack = task.slack_time
        
        # Wait a bit (in real test we'd mock time)
        # For now just verify refresh doesn't crash
        task.refresh_deadline()
        
        assert task.slack_time <= original_slack
    
    def test_to_dict(self):
        """Test serialization to dict."""
        deadline = datetime.now() + timedelta(hours=4)
        task = create_task(
            title="Test task",
            deadline=deadline,
            tags=["urgent", "review"],
        )
        
        d = task.to_dict()
        
        assert d["title"] == "Test task"
        assert d["deadline"] is not None
        assert "urgency_score" in d
        assert "slack_time" in d
        assert "is_overdue" in d
        assert "is_critical" in d
        assert d["tags"] == ["urgent", "review"]


class TestTaskPriority:
    """Test TaskPriority enum."""
    
    def test_priority_values(self):
        """Test priority values."""
        assert TaskPriority.LOW.value == 0.25
        assert TaskPriority.MEDIUM.value == 0.50
        assert TaskPriority.HIGH.value == 0.75
        assert TaskPriority.CRITICAL.value == 1.0


class TestCalculateSchedule:
    """Test schedule calculation."""
    
    def test_schedule_all_fit(self):
        """Test schedule when all tasks fit."""
        tasks = [
            create_task("Task 1", estimated_hours=2.0),
            create_task("Task 2", estimated_hours=3.0),
        ]
        
        result = calculate_schedule(tasks, available_hours=10.0)
        
        assert len(result["scheduled"]) == 2
        assert len(result["dropped"]) == 0
        assert result["total_hours"] == 5.0
    
    def test_schedule_some_dropped(self):
        """Test schedule with overflow."""
        tasks = [
            create_task("Task 1", estimated_hours=8.0),
            create_task("Task 2", estimated_hours=5.0),
        ]
        
        result = calculate_schedule(tasks, available_hours=10.0)
        
        assert len(result["scheduled"]) == 1
        assert len(result["dropped"]) == 1
        assert result["scheduled"][0].title == "Task 1"
    
    def test_schedule_prioritizes_urgent(self):
        """Test that urgent tasks are prioritized."""
        tasks = [
            create_task("Low priority", estimated_hours=2.0),  # urgency 0.5
            create_task("High priority", estimated_hours=5.0, 
                       deadline=datetime.now() + timedelta(hours=1)),  # urgency ~0.9
        ]
        
        result = calculate_schedule(tasks, available_hours=5.0)
        
        # High priority should be scheduled first
        assert result["scheduled"][0].title == "High priority"
    
    def test_utilization_calculation(self):
        """Test utilization calculation."""
        tasks = [
            create_task("Task", estimated_hours=5.0),
        ]
        
        result = calculate_schedule(tasks, available_hours=10.0)
        
        assert result["utilization"] == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
