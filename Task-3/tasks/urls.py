from django.urls import path
from . import views

urlpatterns = [
    path("projects/<int:pk>/tasks/new/", views.create_task, name="create_task"),
    path("tasks/<int:pk>/", views.task_detail, name="task_detail"),
    path("tasks/<int:pk>/edit/", views.update_task, name="update_task"),
    path("tasks/<int:pk>/delete/", views.delete_task, name="delete_task"),
]