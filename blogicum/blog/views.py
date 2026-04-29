from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from .models import Category, Post, Comment
from .forms import PostForm, CommentForm

LIMIT_POST = 5

User = get_user_model()


def get_posts_related_models():
    return Post.objects.select_related(
        'author', 'category', 'location'
    ).filter(
        pub_date__date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    )


class UserPostListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self, queryset=None):
        self.author = get_object_or_404(User, username=self.kwargs['username'])

        if self.author == self.request.user:
            return (
                Post.objects.select_related('author', 'category', 'location')
                .filter(author=self.author)
                .annotate(comment_count=Count('comments'))
                .order_by('-pub_date')
            )

        return (
            get_posts_related_models()
            .filter(author=self.author)
            .annotate(comment_count=Count('comments'))
            .order_by('-pub_date')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.author

        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={'username': self.request.user.username}
        )


class PostUpdateView(UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_object(self, queryset=None):
        if not hasattr(self, 'object'):
            return get_object_or_404(
                get_posts_related_models(), pk=self.kwargs['post_id']
            )

        return self.object

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.pk})

    def test_func(self):
        self.object = self.get_object()
        return self.object.author == self.request.user

    def handle_no_permission(self):
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])


class PostDeleteView(UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'

    def get_object(self, queryset=None):
        if not hasattr(self, 'object'):
            return get_object_or_404(
                get_posts_related_models(), pk=self.kwargs['post_id']
            )

        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = {'instance': self.object}

        return context

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={'username': self.request.user.username}
        )

    def test_func(self):
        self.object = self.get_object()
        return self.object.author == self.request.user


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10

    def get_queryset(self):
        return (
            get_posts_related_models()
            .annotate(comment_count=Count('comments'))
            .order_by('-pub_date')
        )


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        return get_object_or_404(
            get_posts_related_models(), pk=self.kwargs['post_id']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')

        return context


class CategoryPostListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(
            Category, slug=self.kwargs['category_slug'], is_published=True
        )

        posts = (
            get_posts_related_models()
            .filter(category__slug=self.kwargs['category_slug'])
            .annotate(comment_count=Count('comments'))
            .order_by('-pub_date')
        )

        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post_id = self.kwargs['post_id']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )


class CommentUpdateView(UserPassesTestMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        if not hasattr(self, 'object'):
            return get_object_or_404(
                Comment.objects.select_related('author'),
                pk=self.kwargs['comment_id'],
                post_id=self.kwargs['post_id'],
            )

        return self.object

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )

    def test_func(self):
        self.object = self.get_object()
        return self.object.author == self.request.user


class CommentDeleteView(UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        if not hasattr(self, 'object'):
            return get_object_or_404(
                Comment.objects.select_related('author'),
                pk=self.kwargs['comment_id'],
                post_id=self.kwargs['post_id'],
            )

        return self.object

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )

    def test_func(self):
        self.object = self.get_object()
        return self.object.author == self.request.user
