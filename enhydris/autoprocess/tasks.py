from enhydris.celery import app


@app.task
def execute_auto_process(auto_process_id, has_non_append_modifications: bool):
    from .models import AutoProcess

    auto_process = AutoProcess.objects.get(id=auto_process_id).as_specific_instance
    auto_process.execute(recalculate=has_non_append_modifications)
