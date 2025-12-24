from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.db.models import Count
from .forms import PostForm, CommentForm
from .models import Post, Category, Comment
from .utils import paginate_queryset  # Новый импорт

User = get_user_model()
POSTS_PER_PAGE = 10


# Утилиты для вынесения повторяющегося кода
def get_published_posts():
    """Получение опубликованных постов с аннотацией количества комментариев"""
    return Post.objects.published() \
        .select_related('author', 'location', 'category') \
        .prefetch_related('comments') \
        .annotate(comment_count=Count('comments')) \
        .order_by('-pub_date')


def get_user_posts(user, current_user=None):
    """Получение постов пользователя с учетом прав доступа"""
    qs = Post.objects.filter(author=user) \
        .select_related('author', 'location', 'category') \
        .prefetch_related('comments') \
        .annotate(comment_count=Count('comments'))
    
    if not (current_user and current_user.is_authenticated and current_user == user):
        qs = qs.filter(is_published=True, pub_date__lte=timezone.now())
    
    return qs.order_by('-pub_date')


class IndexView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'posts'
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        return get_published_posts()


class ProfileView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    context_object_name = 'posts'
    paginate_by = POSTS_PER_PAGE

    def get_profile_user(self):
        return get_object_or_404(
            User, username=self.kwargs['username']
        )

    def get_queryset(self):
        user = self.get_profile_user()
        return get_user_posts(user, self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['profile_user'] = self.get_profile_user()
        return ctx


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'posts'
    paginate_by = POSTS_PER_PAGE

    def get_category(self):
        return get_object_or_404(Category, slug=self.kwargs['category_slug'], is_published=True)

    def get_queryset(self):
        category = self.get_category()
        return (
            Post.objects.published()
            .filter(category=category)
            .select_related('author', 'location', 'category')
            .prefetch_related('comments')
            .annotate(comment_count=Count('comments'))
            .order_by('-pub_date')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['category'] = self.get_category()
        return ctx


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        obj = get_object_or_404(
            Post.objects.select_related('author', 'location', 'category')
            .annotate(comment_count=Count('comments')),
            id=self.kwargs['post_id']
        )
        visible = obj.is_published and obj.pub_date <= timezone.now()
        if not visible and not (self.request.user.is_authenticated and self.request.user == obj.author):
            raise Http404('Публикация недоступна.')
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        post = ctx['post']
        ctx['form'] = ctx.get('form') or CommentForm()
        ctx['comments'] = post.comments.select_related('author').all()
        return ctx


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user
        if not form.cleaned_data.get('pub_date'):
            post.pub_date = timezone.now()
        post.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


class ProfileRedirectLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


class ProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    fields = ('username', 'first_name', 'last_name', 'email')
    template_name = 'blog/profile_edit.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'profile_user'

    def test_func(self):
        return self.request.user.username == self.kwargs['username']

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.object.username})


class OwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        obj = get_object_or_404(Post, id=self.kwargs['post_id'])
        return (self.request.user.is_authenticated and obj.author == self.request.user)

    def handle_no_permission(self):
        try:
            obj = self.get_object()
            return redirect('blog:post_detail', post_id=obj.id)
        except Exception:
            raise PermissionDenied


class PostUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.id})


class PostDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/detail.html'

    def form_valid(self, form):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        comment = form.save(commit=False)
        comment.post = post
        comment.author = self.request.user
        comment.save()
        return redirect('blog:post_detail', post_id=post.id)

    def form_invalid(self, form):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        return self.render_to_response({
            'post': post,
            'form': form,
            'comments': post.comments.select_related('author').all()
        })


class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    context_object_name = 'comment'

    def get_object(self, queryset=None):
        return get_object_or_404(Comment, id=self.kwargs['comment_id'])

    def test_func(self):
        comment = get_object_or_404(Comment, id=self.kwargs['comment_id'])
        return comment.author == self.request.user

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.post_id})


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    context_object_name = 'comment'

    def get_object(self, queryset=None):
        return get_object_or_404(Comment, id=self.kwargs['comment_id'])

    def test_func(self):
        comment = get_object_or_404(Comment, id=self.kwargs['comment_id'])
        return comment.author == self.request.user

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.post_id})