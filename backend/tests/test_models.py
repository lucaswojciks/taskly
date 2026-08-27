"""Integration test: core models and their relationships against the test DB."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, Task, TaskStatus, User


async def test_project_task_relationships(db_session: AsyncSession) -> None:
    user = User(email="alice@example.com", hashed_password="hashed")
    db_session.add(user)
    await db_session.flush()

    project = Project(name="Website revamp", owner_id=user.id)
    db_session.add(project)
    await db_session.flush()

    task = Task(
        project_id=project.id,
        title="Design the landing page",
        short_description="Landing page mockups",
        full_description="Produce high-fidelity mockups for the new landing page.",
    )
    db_session.add(task)
    await db_session.flush()

    # status has a Python-side default applied on flush
    assert task.status == TaskStatus.not_started

    # forward relationship: task -> project
    await db_session.refresh(task, ["project"])
    assert task.project.id == project.id

    # back_populates: project -> tasks
    await db_session.refresh(project, ["tasks", "owner"])
    assert project.tasks == [task]
    assert project.owner.id == user.id

    # back_populates: user -> projects
    await db_session.refresh(user, ["projects"])
    assert user.projects == [project]
