from django.urls import path, include

from . import views

urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path(
        'registration/',
        views.UserCreateView.as_view(),
        name='registration',
    ),
    path('<slug:username>/', views.UserListView.as_view(), name='user_detail'),
]
