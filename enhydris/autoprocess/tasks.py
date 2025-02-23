from enhydris.celery import app


@app.task
def execute_auto_process(auto_process_id):
    from .models import AutoProcess

    AutoProcess.objects.get(id=auto_process_id).as_specific_instance.execute()
