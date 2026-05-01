from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.http import Http404

from .models import Category, Post, Comment
from .forms import PostForm, CommentForm, UserForm
from blogicum.settings import POSTS_PER_PAGE
from .querysets import get_posts_related_models

User = get_user_model()


class OnlyAuthorMixin(UserPassesTestMixin):
    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user

    def handle_no_permission(self):
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])


class UserPostListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = POSTS_PER_PAGE

    def get_author(self):
        if not hasattr(self, 'author'):
            self.author = get_object_or_404(
                User, username=self.kwargs['username']
            )

        return self.author

    def get_queryset(self, queryset=None):
        author = self.get_author()

        if author == self.request.user:
            return get_posts_related_models(
                Post.objects, is_annotate_and_order=True
            ).filter(author=self.author)

        return get_posts_related_models(
            Post.objects, is_published=True, is_annotate_and_order=True
        ).filter(author=self.author)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_author()

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
            self.object = get_object_or_404(
                get_posts_related_models(Post.objects),
                pk=self.kwargs['post_id'],
            )

        return self.object

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.pk})


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'

    def get_object(self, queryset=None):
        if not hasattr(self, 'object'):
            self.object = get_object_or_404(
                get_posts_related_models(Post.objects),
                pk=self.kwargs['post_id'],
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
        return get_posts_related_models(
            Post.objects, is_published=True, is_annotate_and_order=True
        )


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        post = get_object_or_404(
            get_posts_related_models(Post.objects), pk=self.kwargs['post_id']
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

    def get_category(self):
        if not hasattr(self, 'category'):
            self.category = get_object_or_404(
                Category, slug=self.kwargs['category_slug'], is_published=True
            )

        return self.category

    def get_queryset(self):
        self.get_category()

        return get_posts_related_models(
            Post.objects, is_published=True, is_annotate_and_order=True
        ).filter(category__slug=self.kwargs['category_slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.get_category()
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
            get_posts_related_models(Post.objects), pk=self.kwargs['post_id']
        )

        return super().form_valid(form)


class CommentUpdateView(CommentMixin, OnlyAuthorMixin, UpdateView):
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        if not hasattr(self, 'object'):
            self.object = get_object_or_404(
                Comment.objects.select_related('author'),
                pk=self.kwargs['comment_id'],
                post_id=self.kwargs['post_id'],
            )

        return self.object


class CommentDeleteView(CommentMixin, OnlyAuthorMixin, DeleteView):
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        if not hasattr(self, 'object'):
            self.object = get_object_or_404(
                Comment.objects.select_related('author'),
                pk=self.kwargs['comment_id'],
                post_id=self.kwargs['post_id'],
            )

        return self.object
