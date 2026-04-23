from django.contrib import admin

from blog.models import Category, Location, Post


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'author',
        'category',
        'location',
        'is_published',
        'pub_date',
        'created_at',
    )

    list_editable = (
        'author',
        'category',
        'is_published',
        'location',
        'pub_date',
    )

    list_filter = ('category', 'author', 'location')
    search_fields = ('title',)


class PostInline(admin.StackedInline):
    model = Post
    extra = 0


class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'slug',
        'is_published',
        'created_at',
    )

    list_editable = ('is_published',)
    search_fields = ('title',)
    inlines = (PostInline,)


class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'is_published',
    )

    list_editable = ('is_published',)
    search_fields = ('title',)
    inlines = (PostInline,)


admin.site.empty_value_display = 'Не задано'

admin.site.register(Location, LocationAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Post, PostAdmin)
