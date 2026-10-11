
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Exists, OuterRef

from .models import Profile, Post, Comment, Like, Follow
from .forms import RegisterForm, ProfileForm, PostForm, CommentForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("feed")

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        Profile.objects.get_or_create(user=user)

        login(request, user)
        messages.success(request, "Welcome to ConnectHub!")

        return redirect("feed")

    return render(
        request,
        "social/register.html",
        {"form": form},
    )


@login_required
def feed(request):
    form = PostForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()

        messages.success(request, "Your post has been published!")
        return redirect("feed")

    posts = (
        Post.objects
        .select_related("author")
        .prefetch_related("comments__author", "likes")
        .annotate(
            is_liked=Exists(
                Like.objects.filter(
                    post=OuterRef("pk"),
                    user=request.user,
                )
            )
        )
    )

    following_ids = Follow.objects.filter(
        follower=request.user
    ).values_list("following_id", flat=True)

    return render(
        request,
        "social/feed.html",
        {
            "posts": posts,
            "form": form,
            "following_ids": following_ids,
        },
    )


@login_required
def profile_view(request, username):
    person = get_object_or_404(User, username=username)

    profile, _ = Profile.objects.get_or_create(user=person)

    if request.user == person:
        form = ProfileForm(
            request.POST or None,
            request.FILES or None,
            instance=profile,
        )

        if request.method == "POST" and form.is_valid():
            form.save()

            messages.success(request, "Profile updated!")

            return redirect(
                "profile",
                username=person.username,
            )
    else:
        form = None

    posts = (
        person.posts
        .select_related("author")
        .prefetch_related("comments__author", "likes")
        .annotate(
            is_liked=Exists(
                Like.objects.filter(
                    post=OuterRef("pk"),
                    user=request.user,
                )
            )
        )
    )

    return render(
        request,
        "social/profile.html",
        {
            "person": person,
            "profile": profile,
            "posts": posts,
            "form": form,
            "followers_count": person.followers.count(),
            "following_count": person.following.count(),
            "is_following": Follow.objects.filter(
                follower=request.user,
                following=person,
            ).exists(),
        },
    )


@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()

    return redirect(request.POST.get("next") or "feed")


@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    like, created = Like.objects.get_or_create(
        post=post,
        user=request.user,
    )

    if not created:
        like.delete()

    return redirect(request.POST.get("next") or "feed")


@login_required
@require_POST
def toggle_follow(request, username):
    person = get_object_or_404(User, username=username)

    if person == request.user:
        messages.error(request, "You cannot follow yourself.")

        return redirect(
            "profile",
            username=username,
        )

    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=person,
    )

    if not created:
        follow.delete()

    return redirect(
        "profile",
        username=person.username,
    )


@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        messages.error(
            request,
            "You can only delete your own posts.",
        )
    else:
        post.delete()
        messages.success(request, "Post deleted.")

    return redirect(request.POST.get("next") or "feed")
