from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("projects/new/", views.create_project, name="create_project"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/<int:pk>/members/", views.add_member, name="add_member"),
    path("projects/<int:pk>/delete/", views.delete_project, name="delete_project"),
]