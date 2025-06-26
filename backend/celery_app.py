from celery import Celery
import os

# Central Celery application shared by the API and worker processes.
# The broker and backend default to the standard local Redis instance.
# Configure with environment variables when deploying (e.g. in Docker or cloud).

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", BROKER_URL)

celery_app = Celery(
    "house_sim",
    broker=BROKER_URL,
    backend=BACKEND_URL,
    include=["backend.tasks"],
)

# Configure Celery
celery_app.conf.update(
    # Task routing
    task_default_queue="house_sim_tasks",
    task_routes={
        "backend.tasks.run_simulation": {"queue": "house_sim_tasks"},
    },
    
    # Broker settings
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Task execution settings
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
) 