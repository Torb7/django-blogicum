from django.utils import timezone
from django.shortcuts import render, get_object_or_404

from .models import Category, Post

LIMIT_POST = 5


def get_posts_related_models():
    return Post.objects.select_related(
        'author', 'category', 'location'
    ).filter(
        pub_date__date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    )


def index(request):
    post_list = get_posts_related_models()[:LIMIT_POST]

    context = {'post_list': post_list}

    return render(request, 'blog/index.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True
    )

    post_list = get_posts_related_models().filter(
        category__slug=category_slug,
    )

    context = {'category': category, 'post_list': post_list}

    return render(request, 'blog/category.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(get_posts_related_models(), pk=post_id)

    context = {'post': post}

    return render(request, 'blog/detail.html', context)
