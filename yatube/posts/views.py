from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_list_or_404, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Post
from yatube.settings import COUNT_PAGINATOR_PAGE

User = get_user_model()


class IndexView(ListView):
    model = Post
    template_name = 'posts/index.html'
    paginate_by = COUNT_PAGINATOR_PAGE


class GroupPostView(ListView):
    model = Post
    template_name = 'posts/group_list.html'
    paginate_by = COUNT_PAGINATOR_PAGE

    def get_queryset(self):
        return get_list_or_404(Post, group__slug=self.kwargs['slug'])


class ProfileDetailView(ListView):
    model = Post
    paginate_by = COUNT_PAGINATOR_PAGE
    template_name = 'posts/profile.html'

    def get_queryset(self):
        return (
            Post.objects.select_related('author')
            .filter(author__username=self.kwargs['username'])
        )

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["author"] = get_object_or_404(
            User, username=self.kwargs['username']
        )
        if (
            Follow.objects.filter(
                user__username=self.request.user,
                author__username=self.kwargs['username']).exists()
        ):
            context["following"] = True
        return context


class PostDetailView(CreateView):
    form_class = CommentForm
    template_name = 'posts/post_detail.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["post"] = get_object_or_404(Post, pk=self.kwargs['post_id'])
        context["comments"] = context["post"].comment.all()
        return context


class PostCreate(LoginRequiredMixin, CreateView):
    form_class = PostForm
    template_name = 'posts/create_post.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()
        return super().form_valid(form)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = False
        return context


class PostEdit(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    pk_url_kwarg = 'post_id'
    template_name = 'posts/create_post.html'

    def get_success_url(self):
        return reverse('posts:post_detail', args=[self.kwargs['post_id']])

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context


class PostDelete(LoginRequiredMixin, DeleteView):
    model = Post
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        username = (
            get_object_or_404(Post, pk=self.kwargs['post_id'])
            .author.username
        )
        return reverse('posts:profile', args=[username])


class CommentCreate(LoginRequiredMixin, CreateView):
    template_name = 'posts/post_detail.html'
    form_class = CommentForm
    pk_url_kwarg = 'post_id'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        self.object.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(
            self.request,
            messages.WARNING,
            *form.errors.values())
        return redirect('posts:post_detail', self.kwargs['post_id'])


class FollowIndex(LoginRequiredMixin, ListView):
    template_name = 'posts/follow.html'
    paginate_by = COUNT_PAGINATOR_PAGE

    def get_queryset(self):
        authors = Follow.objects.filter(user=self.request.user)
        posts = Post.objects.filter(
            author__in=[author.author.id for author in authors]
        )
        return posts


class ProfileFollow(LoginRequiredMixin, UpdateView):
    def get(self, request, username):
        author = get_object_or_404(User, username=username)
        follow_create = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
        if not follow_create and author != request.user:
            Follow.objects.create(user=request.user, author=author)
        return HttpResponseRedirect(reverse('posts:follow_index'))


class ProfileUnfollow(LoginRequiredMixin, UpdateView):
    def get(self, request, username):
        author = get_object_or_404(User, username=username)
        follow_delet = get_object_or_404(
            Follow,
            user=request.user, author=author
        )
        if follow_delet:
            follow_delet.delete()
        return HttpResponseRedirect(reverse('posts:follow_index'))
