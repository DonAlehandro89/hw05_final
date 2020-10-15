from django import forms
from django.forms import ModelForm
from .models import Post, Group, Comment


class PostForm(ModelForm):

    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        help_texts = {
            'group': 'Выберите группу, к которой вы бы хотели отнести свой текст,\
                       данное поле заполнять не обязательно'
        }
        labels = {
            'group': 'Группа',
            'text': 'Текст',
            'image': 'Картинка'
        }

class CommentForm(ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        text = forms.CharField(widget=forms.Textarea)
    

