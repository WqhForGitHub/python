"""
博客相关表单：文章、评论、搜索。
"""

from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """文章创建/编辑表单。"""

    class Meta:
        model = Post
        fields = ("title", "excerpt", "content", "cover", "tags", "is_published")
        labels = {
            "title": "标题",
            "excerpt": "摘要",
            "content": "正文",
            "cover": "封面图",
            "tags": "标签",
            "is_published": "已发布",
        }
        widgets = {
            "excerpt": forms.TextInput(attrs={"placeholder": "一句话摘要（可选）"}),
            "content": forms.Textarea(
                attrs={"rows": 12, "placeholder": "支持纯文本..."}
            ),
            "tags": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 让标签字段非必填
        self.fields["tags"].required = False
        self.fields["cover"].required = False


class CommentForm(forms.ModelForm):
    """评论表单。"""

    class Meta:
        model = Comment
        fields = ("content",)
        labels = {"content": "评论内容"}
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "说点什么...",
                    "class": "form-control",
                }
            ),
        }


class SearchForm(forms.Form):
    """搜索表单。"""

    q = forms.CharField(
        label="搜索",
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "搜索文章...",
                "class": "form-control",
            }
        ),
    )
