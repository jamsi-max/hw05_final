from django.forms import ModelForm

from posts.models import Post, Comment


class PostForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].empty_label = 'Категория не выбрана'

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

        help_texts = {
            'group': 'Группа, к которой будет относиться пост',
            'text': 'Текст нового поста',
        }
        labels = {
            'text': 'Текст поста',
            'group': 'Выбор группы',
        }


class CommentForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].empty_label = 'Комментарий не должен быть пустым'

    class Meta:
        model = Comment
        fields = ('text',)
