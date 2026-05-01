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
from django.http import Http404

from .models import Category, Post, Comment
from .forms import PostForm, CommentForm, UserForm
from blogicum.settings import POSTS_PER_PAGE

User = get_user_model()


def get_posts_related_models():
    return Post.objects.select_related(
        'author', 'category', 'location'
    ).filter(
        pub_date__date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    )


class OnlyAuthorMixin(UserPassesTestMixin):
    def test_func(self):
        self.object = self.get_object()
        return self.object.author == self.request.user

    def handle_no_permission(self):
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])


class UserPostListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = POSTS_PER_PAGE

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


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={'username': self.object.username}
        )


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


class PostUpdateView(OnlyAuthorMixin, UpdateView):
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


class PostDeleteView(OnlyAuthorMixin, DeleteView):
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
        context['form'] = PostForm(instance=self.object)

        return context

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={'username': self.request.user.username}
        )


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = POSTS_PER_PAGE

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
        post = get_object_or_404(
            Post.objects.select_related('author', 'category', 'location'),
            pk=self.kwargs['post_id'],
        )

        if post.author != self.request.user:
            if (
                post.pub_date > timezone.now()
                or not post.is_published
                or not post.category.is_published
            ):
                raise Http404()

        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')

        return context


class CategoryPostListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = POSTS_PER_PAGE

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


class CommentMixin:
    model = Comment

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )


class CommentCreateView(CommentMixin, LoginRequiredMixin, CreateView):
    form_class = CommentForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            get_posts_related_models(), pk=self.kwargs['post_id']
        )

        return super().form_valid(form)


class CommentUpdateView(CommentMixin, OnlyAuthorMixin, UpdateView):
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


class CommentDeleteView(CommentMixin, OnlyAuthorMixin, DeleteView):
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        if not hasattr(self, 'object'):
            return get_object_or_404(
                Comment.objects.select_related('author'),
                pk=self.kwargs['comment_id'],
                post_id=self.kwargs['post_id'],
            )

        return self.object
