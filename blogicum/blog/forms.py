from django import forms

from blog.models import Comment, Post, User

from django.core.mail import send_mail

send_mail(
    subject="Тема письма",
    message="Текст сообщения",
    from_email="from@example.com",
    recipient_list=["to@example.com"],
    fail_silently=True,
)


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        exclude = ("author",)
        widgets = {"pub_date": forms.DateInput(attrs={"type": "date"})}


class UserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = "__all__"


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ("text",)
