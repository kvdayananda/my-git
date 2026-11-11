"""Tests for TaskPulse Dispatcher."""
from app.core import Job, JobQueue
from app.main import TaskPulseEngine


def test_priority_queueing():
    q = JobQueue()
    q.enqueue(Job("1", "low_job", priority=1))
    q.enqueue(Job("2", "high_job", priority=3))
    q.enqueue(Job("3", "mid_job", priority=2))

    first = q.pop_next()
    assert first.id == "2"
    second = q.pop_next()
    assert second.id == "3"


def test_retry_mechanism():
    engine = TaskPulseEngine()
    engine.submit_job("j1", "test_job", priority=2)

    def failing_executor(job):
        raise RuntimeError("Transient network timeout")

    status = engine.run_worker_cycle(failing_executor)
    assert status == "failed_or_requeued"
    job = engine.queue.jobs[0]
    assert job.retries_left == 2
    assert job.status == "queued"
