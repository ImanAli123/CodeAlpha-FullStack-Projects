
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.feed, name="feed"),
    path("register/", views.register_view, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="social/login.html"
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path("profile/<str:username>/", views.profile_view, name="profile"),
    path("comment/<int:post_id>/", views.add_comment, name="comment"),
    path("like/<int:post_id>/", views.toggle_like, name="like"),
    path("follow/<str:username>/", views.toggle_follow, name="follow"),
    path("delete/<int:post_id>/", views.delete_post, name="delete_post"),
]
