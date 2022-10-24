from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm

POSTS_QUANTITY: int = 10


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related('author', 'group')
    paginator = Paginator(posts, POSTS_QUANTITY)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'page_obj': page_obj
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    paginator = Paginator(group.posts.all(), POSTS_QUANTITY)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, template, context)


def profile(request, username):
    following = False
    template = 'posts/profile.html'
    user = get_object_or_404(User, username=username)
    posts = user.posts.select_related('author', 'group')
    paginator = Paginator(posts, POSTS_QUANTITY)
    page_obj = paginator.get_page(request.GET.get('page'))

    if not request.user.is_anonymous:
        if Follow.objects.filter(user=request.user, author=user):
            following = True

    context = {
        'author': user,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.select_related('author')
    context = {
        'post': post,
        'form': CommentForm(),
        'comments': comments
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )

    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', request.user.username)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if request.user != post.author:
        return redirect('posts:post_detail', post_id)

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)

    context = {
        'is_edit': True,
        'form': form,
        'post': post
    }
    return render(request, template, context)


@login_required
def follow_index(request):
    posts = []
    for follow in request.user.follower.select_related('author'):
        query_set = follow.author.posts.select_related('group', 'author')
        for post in query_set:
            posts.append(post)

    paginator = Paginator(posts, POSTS_QUANTITY)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(
        request,
        'posts/follow.html',
        context={'page_obj': page_obj}
    )


@login_required
def profile_follow(request, username):
    if request.user.username != username:
        author = get_object_or_404(User, username=username)
        if not request.user.follower.filter(author=author):
            Follow.objects.create(
                user=request.user,
                author=author
            )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=username)
    follow_link = request.user.follower.filter(author=user)
    if follow_link:
        follow_link.delete()
    return redirect('posts:profile', username=username)
