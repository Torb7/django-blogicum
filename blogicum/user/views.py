from django.views.generic import ListView, CreateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy


from blog.models import Post

User = get_user_model()


class UserListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self, queryset=None):
        self.user = get_object_or_404(User, username=self.kwargs['username'])

        posts = Post.objects.select_related(
            'author', 'category', 'location'
        ).filter(author=self.user)

        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.user

        return context


class UserCreateView(CreateView):
    form_class = UserCreationForm
    template_name = "registration/registration_form.html"
    success_url = reverse_lazy("blog:index")
