from django.contrib import admin
from django.conf import settings
from django.urls import path, include

handler404 = 'pages.views.page_not_found'
handler500 = 'pages.views.server_error'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('user.urls')),
    path('', include('blog.urls')),
    path('pages/', include('pages.urls')),
    path('profile/', include('user.urls')),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)
