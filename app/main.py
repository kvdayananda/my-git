"""TaskPulse Main Entry Point."""
from app.core import Job, JobQueue


class TaskPulseEngine:
    def __init__(self) -> None:
        self.queue = JobQueue()

    def submit_job(self, job_id: str, name: str, priority: int = 1) -> Job:
        job = Job(id=job_id, name=name, priority=priority)
        self.queue.enqueue(job)
        return job

    def run_worker_cycle(self, executor: callable) -> str:
        job = self.queue.pop_next()
        if not job:
            return "idle"
        try:
            executor(job)
            self.queue.complete_job(job.id)
            return "succeeded"
        except Exception as e:
            self.queue.fail_job(job.id, str(e))
            return "failed_or_requeued"
