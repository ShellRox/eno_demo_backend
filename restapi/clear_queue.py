import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "restapi.settings")
django.setup()

from background_task.models import Task, CompletedTask

Task.objects.all().delete()
CompletedTask.objects.all().delete()
