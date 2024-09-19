
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from blog.forms import CommentForm, PostForm, UserForm
from blog.models import Category, Comment, Post, User
from django.http import Http404


class IndexListView(ListView):
    model = Post
    template_name = "blog/index.html"
    ordering = "-pub_date"
    paginate_by = 10

    queryset = (
        Post.objects.prefetch_related("comments")
        .select_related("author")
        .filter(
            pub_date__lt=timezone.now(),
            is_published=True,
            category__is_published=True,
        )
        .annotate(comment_count=Count("comments"))
    )


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/detail.html"
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = get_object_or_404(Post, pk=self.kwargs.get("post_id"))
        if post.author != self.request.user and not post.is_published:
            raise Http404
        context["form"] = CommentForm()
        context["comments"] = Comment.objects.prefetch_related("post").filter(
            post=post)
        return context


class CategoryListView(ListView):
    model = Post
    template_name = "blog/category.html"
    paginate_by = 10
    ordering = "-pub_date"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = get_object_or_404(
            Category,
            slug=self.kwargs["category_slug"],
            is_published=True,
        )
        return context

    def get_queryset(self):
        category_slug = self.kwargs.get("category_slug")
        category = get_object_or_404(Category, slug=category_slug,
                                     is_published=True)

        queryset = (
            category.posts.filter(
                pub_date__lt=timezone.now(),
                is_published=True,
            )
            .annotate(comment_count=Count("comments"))
            .order_by("-pub_date")
        )
        return queryset


class ProfileListView(ListView):
    model = Post
    template_name = "blog/profile.html"
    ordering = "id"
    paginate_by = 10
    username = None

    def get_queryset(self):
        self.username = self.kwargs.get("username")
        author = get_object_or_404(User, username=self.kwargs.get("username"))
        instance = (
            author.posts.filter(author__username__exact=self.username)
            .annotate(comment_count=Count("comments"))
            .order_by("-pub_date")
        )
        return instance

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = get_object_or_404(User, username=self.username)
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/create.html"

    def get_success_url(self):
        return reverse_lazy("blog:profile", kwargs={"username":
                                                    self.request.user})

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "blog/create.html"
    pk_url_kwarg = "post_id"
    posts = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context

    def dispatch(self, request, *args, **kwargs):
        self.posts = get_object_or_404(Post, pk=kwargs.get("post_id"))
        if self.posts.author != request.user:
            return redirect("blog:post_detail", self.kwargs.get("post_id"))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("blog:post_detail", kwargs={"post_id":
                                                        self.posts.pk})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = "blog/create.html"
    success_url = reverse_lazy("blog:index")
    pk_url_kwarg = "post_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_delete"] = True
        return context

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, pk=kwargs.get("post_id"))
        if instance.author != request.user:
            return redirect("blog:post_detail", self.kwargs.get("post_id"))
        return super().dispatch(request, *args, **kwargs)


class CommentEditMixin:
    model = Comment
    pk_url_kwarg = "comment_id"
    template_name = "blog/comment.html"

    def get_success_url(self):
        return reverse("blog:post_detail", args=[self.kwargs["post_id"]])


class CommentCreateView(CommentEditMixin, LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        form.instance.post = get_object_or_404(Post, pk=self.kwargs["post_id"])
        form.instance.author = self.request.user
        return super().form_valid(form)


class CommentDeleteView(CommentEditMixin, LoginRequiredMixin, DeleteView):
    model = Comment
    pk_url_kwarg = "comment_id"

    def delete(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=self.kwargs[self.pk_url_kwarg])
        if self.request.user != comment.author:
            return redirect("blog:post_detail", post_id=self.kwargs["post_id"])
        return super().delete(request, *args, **kwargs)


class CommentUpdateView(CommentEditMixin, LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    pk_url_kwarg = "comment_id"

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=self.kwargs[self.pk_url_kwarg])
        if self.request.user != comment.author:
            return redirect("blog:post_detail", post_id=self.kwargs["post_id"])

        return super().dispatch(request, *args, **kwargs)


class ProfiletUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = "blog/user.html"
    success_url = reverse_lazy("blog:index")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "blog:profile", kwargs={"username": self.request.user.username}
        )
