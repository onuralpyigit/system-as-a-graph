"""
Description: Job-queue adapters that run Model Setup Data production outside the request.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from vae.operations_panel.src.model.production_job import (
    ProductionJob,
    ProductionJobRequest,
)


class ProductionRunner(Protocol):
    """Whatever can execute a queued production process."""

    def run(self, request: ProductionJobRequest) -> ProductionJob:
        """Execute the process and record its outcome."""
        ...


class ImmediateJobQueue:
    """Runs the production process inline, before ``enqueue`` returns.

    Used where no database-backed queue is configured, and in tests. The
    "in progress" state still exists in the job record — it is simply never
    observed from outside, because the work is already done by the time the
    caller can look.
    """

    def __init__(self, runner: Callable[[], ProductionRunner]) -> None:
        """Initialize the queue.

        Args:
            runner: Resolves the executor when a job is queued. Resolved late
                because the executor and this queue are each other's
                collaborators, and neither can be built first.
        """
        self._runner = runner

    def enqueue(self, request: ProductionJobRequest) -> None:
        """Run the production process now."""
        self._runner().run(request)


class ProcrastinateJobQueue:
    """Defers the production process to a Procrastinate worker.

    This is what makes VAE-01.6's three statuses real: the request returns as
    soon as the job row exists, a separate worker process picks the job up, and
    the operator sees "in progress" until that worker finishes. It also keeps
    concurrent production runs isolated from one another, which the same
    worker pool gives for free.
    """

    def __init__(self, app, task_name: str) -> None:
        """Initialize the queue.

        Args:
            app: The configured Procrastinate application.
            task_name: Name the production task is registered under.
        """
        self._app = app
        self._task_name = task_name

    def enqueue(self, request: ProductionJobRequest) -> None:
        """Defer the production process to the worker pool.

        Args:
            request: What to produce, and which job row to update.
        """
        with self._app.open():
            self._app.configure_task(name=self._task_name).defer(
                job_id=request.job_id,
                project=request.system_version.project.name,
                platform=request.system_version.platform.name,
                system_version=request.system_version.version,
                started_by=request.started_by,
                run_id=request.run_id,
            )
