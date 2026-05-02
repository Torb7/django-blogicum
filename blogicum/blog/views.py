from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .models import Category, Post
from .forms import PostForm, CommentForm, UserForm
from blogicum.settings import POSTS_PER_PAGE
from .querysets import get_posts_related_models
from .mixins import OnlyAuthorMixin, CommentMixin

User = get_user_model()


class UserPostListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = POSTS_PER_PAGE

    def get_author(self):
        # Убрал кеширование, но не понимаю зачем дублировать запрос в БД?
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self, queryset=None):
        author = self.get_author()

        is_published = not author == self.request.user

        return get_posts_related_models(
            author.posts, is_published=is_published, is_annotate_and_order=True
        )

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
    queryset = get_posts_related_models()
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.pk})


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    model = Post
    queryset = get_posts_related_models()
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

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
            is_published=True, is_annotate_and_order=True
        )


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        post = get_object_or_404(
            get_posts_related_models(), pk=self.kwargs['post_id']
        )

        if post.author != self.request.user:
            # Исправил, но тут так же дублирующий запрос в БД, в Django
            # документации указано, что надо работать с уже полученным
            # объектом.
            return get_object_or_404(
                get_posts_related_models(
                    is_published=True, is_annotate_and_order=True
                ),
                pk=self.kwargs['post_id'],
            )

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
        return get_object_or_404(
            Category, slug=self.kwargs['category_slug'], is_published=True
        )

    def get_queryset(self):
        category = self.get_category()

        return get_posts_related_models(
            category.posts, is_published=True, is_annotate_and_order=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.get_category()
        return context


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


class CommentDeleteView(CommentMixin, OnlyAuthorMixin, DeleteView):
    template_name = 'blog/comment.html'
