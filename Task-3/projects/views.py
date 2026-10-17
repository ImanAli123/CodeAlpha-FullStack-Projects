from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import Project
from .forms import ProjectForm
from tasks.models import Task


@login_required
def dashboard(request):
    projects = Project.objects.filter(
        members=request.user
    ).distinct().order_by("-created_at")

    return render(request, "dashboard.html", {
        "projects": projects,
    })


@login_required
def create_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST, user=request.user)

        if form.is_valid():
            project = form.save(commit=False)
            project.creator = request.user
            project.save()
            form.save_m2m()
            project.members.add(request.user)
            return redirect("project_detail", pk=project.pk)
    else:
        form = ProjectForm(user=request.user)

    return render(request, "project_form.html", {"form": form})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(
        Project.objects.filter(members=request.user),
        pk=pk,
    )

    tasks = project.tasks.select_related(
        "assigned_to", "created_by"
    ).prefetch_related("comments__author")

    return render(request, "project_detail.html", {
        "project": project,
        "todo_tasks": tasks.filter(status="todo"),
        "progress_tasks": tasks.filter(status="progress"),
        "done_tasks": tasks.filter(status="done"),
    })


@login_required
def add_member(request, pk):
    project = get_object_or_404(
        Project.objects.filter(members=request.user),
        pk=pk,
    )

    if project.creator != request.user:
        return redirect("project_detail", pk=pk)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        member = User.objects.filter(username=username).first()

        if member:
            project.members.add(member)

    return redirect("project_detail", pk=pk)


@login_required
def delete_project(request, pk):
    project = get_object_or_404(
        Project, pk=pk, creator=request.user
    )

    if request.method == "POST":
        project.delete()
        return redirect("dashboard")

    return redirect("project_detail", pk=pk)