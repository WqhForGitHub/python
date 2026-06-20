"""Blog forms - 文章与评论表单"""

from django import forms

from .models import Article, Comment


class ArticleForm(forms.ModelForm):
    """文章发布/编辑表单"""

    class Meta:
        model = Article
        fields = ['title', 'body']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入标题'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 15, 'placeholder': '请输入正文'}),
        }
        labels = {
            'title': '标题',
            'body': '正文',
        }


class CommentForm(forms.ModelForm):
    """评论表单"""

    class Meta:
        model = Comment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': '写下你的评论...'}
            ),
        }
        labels = {
            'body': '',
        }
