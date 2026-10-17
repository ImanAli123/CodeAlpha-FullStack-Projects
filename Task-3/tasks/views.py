from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from projects.models import Project
from .models import Task, Comment
from .forms import TaskForm, CommentForm


def get_member_project(request, pk):
    return get_object_or_404(
        Project.objects.filter(members=request.user),
        pk=pk,
    )


@login_required
def create_task(request, pk):
    project = get_member_project(request, pk)

    if request.method == "POST":
        form = TaskForm(request.POST, project=project)

        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.created_by = request.user
            task.save()
            return redirect("project_detail", pk=project.pk)
    else:
        form = TaskForm(project=project)

    return render(request, "task_form.html", {
        "form": form,
        "project": project,
    })


@login_required
def task_detail(request, pk):
    task = get_object_or_404(
        Task.objects.filter(project__members=request.user),
        pk=pk,
    )

    if request.method == "POST":
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()
            return redirect("task_detail", pk=task.pk)
    else:
        form = CommentForm()

    return render(request, "task_detail.html", {
        "task": task,
        "form": form,
    })


@login_required
def update_task(request, pk):
    task = get_object_or_404(
        Task.objects.filter(project__members=request.user),
        pk=pk,
    )

    if request.method == "POST":
        form = TaskForm(
            request.POST,
            instance=task,
            project=task.project,
        )

        if form.is_valid():
            form.save()
            return redirect("project_detail", pk=task.project.pk)
    else:
        form = TaskForm(instance=task, project=task.project)

    return render(request, "task_form.html", {
        "form": form,
        "project": task.project,
        "task": task,
    })


@login_required
def delete_task(request, pk):
    task = get_object_or_404(
        Task.objects.filter(project__members=request.user),
        pk=pk,
    )
    project_pk = task.project.pk

    if request.method == "POST" and (
        task.created_by == request.user
        or task.project.creator == request.user
    ):
        task.delete()

    return redirect("project_detail", pk=project_pk)