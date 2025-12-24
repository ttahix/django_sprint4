from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Post, Comment

User = get_user_model()


class CustomCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control'

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'location': forms.Select(attrs={
                'class': 'form-control',
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
            }),
        }
        labels = {
            'is_published': 'Опубликовать сейчас',
            'pub_date': 'Дата и время публикации',
            'text': 'Текст поста',
            'title': 'Заголовок',
            'location': 'Местоположение',
            'category': 'Категория',
            'image': 'Изображение',
        }
        help_texts = {
            'is_published': 'Снимите галочку, чтобы скрыть публикацию.',
            'pub_date': 'Если выбрать дату и время в будущем, то публикация будет отложенной.',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pub_date'].required = False
        self.fields['image'].widget.attrs.update({'class': 'form-control'})


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
            }),
        }