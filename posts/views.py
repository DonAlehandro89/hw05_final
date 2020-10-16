from django.shortcuts import render, get_object_or_404
from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm
from django.shortcuts import redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required


def index(request):
    post_list = Post.objects.order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all().order_by("-pub_date")
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "group.html", {
                  "group": group, 'page': page, 'paginator': paginator})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'new_post.html', {'form': form})


@login_required
def add_comment(request,username,post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('post', username = username, post_id = post_id)
    return redirect('post', username = username, post_id = post_id)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    #f = get_object_or_404(Follow, user=request.user, author=author)
    following = False
    if request.user.is_authenticated:
        if Follow.objects.filter(author__username=username, user=request.user):
            following = True
    post_list = author.posts.all().order_by("-pub_date")
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'profile.html', {
        'page': page,
        'paginator': paginator,
        'author': author,
        'following': following
    })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm()
    return render(request, 'post.html', {'author': post.author,
                                         'post': post,
                                         'form': form})


def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user != post.author:
        return redirect('post', username=author.username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        post = form.save()
        return redirect('post',
                        username=request.user.username,
                        post_id=post_id)
    return render(request,
                  'new_post.html',
                  {'form': form,
                   'post': post,
                   'is_edit': True
                   })


@login_required
def follow_index(request):
    post_list = Post.objects.filter(
        author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html",{'page': page,
                                         'paginator': paginator})


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(author__username=username, user=request.user).delete()
    return redirect('index')


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    is_follow = Follow.objects.filter(author__username=username,
                                       user=request.user).exists()
    if request.user != author and not is_follow:
        Follow.objects.create(author=author,
                                        user=request.user)
    return redirect('index')


def page_not_found(request, exception):
    return render(
        request, 
        "misc/404.html", 
        {"path": request.path}, 
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500) 


