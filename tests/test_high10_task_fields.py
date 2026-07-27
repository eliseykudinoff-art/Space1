"""Тесты [HIGH-10]: Task typed поля."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from space1.models.task import Task, TaskSource, Attachment, create_task

def test_task_source_enum():
    t = Task("1", "T", source=TaskSource.OWNER_DIRECT)
    assert t.source == TaskSource.OWNER_DIRECT
    assert t.source.value == "OWNER_DIRECT"

def test_task_typed_fields():
    t = Task("1", "T", price=150.0, attachments=[Attachment("f.py", "text/python", 100)])
    assert t.price == 150.0
    assert len(t.attachments) == 1
    assert t.attachments[0].filename == "f.py"

def test_task_capability_vector():
    t = Task("1", "T", capability_vector={"code_gen": 0.9, "design": 0.5})
    assert t.capability_vector["code_gen"] == 0.9

def test_create_task_with_source():
    t = create_task("T", source=TaskSource.OWNER_DIRECT)
    assert t.source == TaskSource.OWNER_DIRECT
