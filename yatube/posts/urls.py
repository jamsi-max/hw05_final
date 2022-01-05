# posts/urls.py
from django.urls import path

from posts.views import (CommentCreate, FollowIndex, GroupPostView, IndexView,
                         PostCreate, PostDelete, PostDetailView, PostEdit,
                         ProfileDetailView, ProfileFollow, ProfileUnfollow)

app_name = 'posts'

urlpatterns = [
    path('', IndexView.as_view(), name='main'),
    path('group/<slug:slug>/', GroupPostView.as_view(), name='group_list'),
    path(
        'profile/<str:username>/',
        ProfileDetailView.as_view(),
        name='profile'),
    path('posts/<int:post_id>/', PostDetailView.as_view(), name='post_detail'),
    path('create/', PostCreate.as_view(), name='post_create'),
    path('posts/<int:post_id>/edit/', PostEdit.as_view(), name='post_edit'),
    path(
        'posts/<int:post_id>/delete/',
        PostDelete.as_view(),
        name='post_delete'),
    path(
        'posts/<int:post_id>/comment/',
        CommentCreate.as_view(),
        name='add_comment'),
    path('follow/', FollowIndex.as_view(), name='follow_index'),
    path(
        'profile/<str:username>/follow/',
        ProfileFollow.as_view(),
        name='profile_follow'
    ),
    path(
        'profile/<str:username>/unfollow/',
        ProfileUnfollow.as_view(),
        name='profile_unfollow'
    ),
]
