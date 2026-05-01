from django.db.models import Count
from django.utils import timezone

from .models import Post


def get_posts_related_models(
    manager=Post.objects, is_published=False, is_annotate_and_order=False
):
    queryset = manager.select_related('author', 'category', 'location')

    if is_published:
        queryset = queryset.filter(
            pub_date__date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        )

    if is_annotate_and_order:
        queryset = queryset.annotate(comment_count=Count('comments')).order_by(
            '-pub_date'
        )

    return queryset
