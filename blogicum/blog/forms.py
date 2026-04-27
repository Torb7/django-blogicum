from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'text', 'category', 'location', 'pub_date', 'image')
        widgets = {
            'pub_date': forms.DateInput(
                attrs={'type': 'date'}, format='%Y-%m-%d'
            )
        }
