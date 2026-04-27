from django.views.generic import ListView, DetailView
from django.db.models import Count
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404

from .models import Category, Post

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
        context['comments'] = self.object.comments.select_related('author')

        return context


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True
    )

    post_list = get_posts_related_models().filter(
        category__slug=category_slug,
    )

    context = {'category': category, 'post_list': post_list}

    return render(request, 'blog/category.html', context)
