"""Boards forms - 看板、列、卡片相关表单"""

from django import forms

from .models import Board, Card, Column


class BoardForm(forms.ModelForm):
    """看板创建 / 编辑表单。"""

    class Meta:
        model = Board
        fields = ("title", "description")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={"rows": 3, "class": "form-control"},
            ),
        }
        labels = {
            "title": "标题",
            "description": "描述",
        }


class ColumnForm(forms.ModelForm):
    """列创建表单。"""

    class Meta:
        model = Column
        fields = ("title",)
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "列表标题"},
            ),
        }
        labels = {
            "title": "标题",
        }


class CardForm(forms.ModelForm):
    """卡片创建 / 编辑表单。"""

    class Meta:
        model = Card
        fields = ("title", "description", "assignee", "priority", "due_date", "labels")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={"rows": 2, "class": "form-control"},
            ),
            "assignee": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "due_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"},
            ),
            "labels": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "多个标签用逗号分隔，如: 前端,紧急",
                },
            ),
        }
        labels = {
            "title": "标题",
            "description": "描述",
            "assignee": "负责人",
            "priority": "优先级",
            "due_date": "截止日期",
            "labels": "标签",
        }


class CardMoveForm(forms.Form):
    """卡片移动表单：指定目标列与新顺序。"""

    card_id = forms.IntegerField(widget=forms.HiddenInput)
    target_column_id = forms.IntegerField(
        label="目标列表",
        widget=forms.Select,
    )
    new_order = forms.IntegerField(
        label="顺序",
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
    )

    def __init__(self, *args, **kwargs):
        # 可传入 board 以填充目标列选项
        board = kwargs.pop("board", None)
        super().__init__(*args, **kwargs)
        if board is not None:
            self.fields["target_column_id"].widget.choices = [
                (column.id, column.title) for column in board.columns.all()
            ]
