from django.test import TestCase, Client, override_settings
from .models import Post, Group, User, Follow, Comment
from django.shortcuts import reverse
from django.core.cache import caches, cache
from django.core.cache.utils import make_template_fragment_key
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.base import File
from PIL import Image
from io import BytesIO


class TestBasicFunctions(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="username1", password='test'
        )
        self.user1 = User.objects.create_user(
            username="username2", password='test'
        )
        self.group = Group.objects.create(title='testtitle', slug='testslug')
        self.group1 = Group.objects.create(
            title='testtitle1', slug='testslug1')
        self.client.force_login(self.user)
        self.client_not_authorized = Client()


    def check_url(self, url, text, author, group):
        attrs = {'text': text, 'author': author, 'group': group}
        response = self.client.get(url)
        if 'page' in response.context:
            post = response.context['page'].object_list[0]
        else:
            post = response.context['post']
        self.assertEqual(response.status_code, 200)
        for attribute in attrs: 
            self.assertEqual(
                getattr(post, attribute),
                attrs[attribute])

    @staticmethod
    def get_image_file(name='test.png', ext='png', size=(50, 50), color=(256, 0, 0)):
        file_obj = BytesIO()
        image = Image.new("RGBA", size=size, color=color)
        image.save(file_obj, ext)
        file_obj.seek(0)
        return File(file_obj, name=name)


    def test_cache(self):
        cache = caches['default']
        key = make_template_fragment_key('index_page')
        self.client.get(reverse('index'))
        self.assertTrue(cache.get(key))

    
    def test_404_err(self):
        text = 'testtesttest'
        response = self.client.get('test/')
        self.assertEqual(response.status_code, 404)


    def test_profile(self):
        response = self.client.get(reverse(
            "profile", args=[
                self.user.username]))
        self.assertEqual(response.status_code, 200)

    def test_new_post_create(self):
        text = 'testtesttest'
        response = self.client.post(
            reverse('new_post'), {
                'text': text,
                'group': self.group.id})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.text, text)
        self.assertEqual(post.group, self.group)

    def test_post(self):
        text = 'testtesttest'
        post = Post.objects.create(text=text, author=self.user,
                                        group=self.group)
        urls = [
            reverse('post', args=[post.author, post.id]),
            reverse('index'),
            reverse("profile", args=[self.user.username]),
            reverse("groups", args=[self.group.slug]),
        ]
        for url in urls:
            self.check_url(url=url, text=text,
                           author=self.user, group=self.group)

    def test_authorized_user_edit_post(self):
        text = 'testtesttest'
        text1 = 'edit_test'
        post = Post.objects.create(text=text1,
                                        author=self.user,
                                        group=self.group1)
        self.client.post(reverse('post_edit',
                                 args=[post.author,
                                       post.id]),
                         {'text': text,
                          'group': self.group.id})
        urls = [
            reverse('post', args=[post.author, post.id]),
            reverse('index'),
            reverse("groups", args=[self.group.slug])
        ]
        for url in urls:
            self.check_url(url=url, text=text,
                           author=self.user, group=self.group)
        response = self.client.get(
                reverse("groups", args=[self.group1.slug])
            )
        self.assertEqual(len(response.context["page"]), 0)


    def test_no_authorized_user_post(self):
        text = 'testtesttest'
        response = self.client_not_authorized.post(
            reverse('new_post'), {
                'text': text})
        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('new_post')}")
        self.assertEqual(Post.objects.count(), 0)
    
    def test_follow(self):
        self.client.post(reverse('profile_follow',
                                 args=[self.user1]),
                         {'author': self.user1,
                          'user': self.user})
        self.assertEqual(Follow.objects.count(), 1)
        follow = Follow.objects.first()
        self.assertEqual(follow.author, self.user1)
        self.assertEqual(follow.user, self.user)


    def test_unfollow(self):
        text = 'testtesttest'
        url = reverse('follow_index')
        Post.objects.create(text=text, author=self.user1,
                                        group=self.group)
        self.client.post(reverse('profile_follow',
                                 args=[self.user1]),
                         {'author': self.user1,
                          'user': self.user})
        self.client.get(reverse('profile_unfollow',
                                 args=[self.user1]),
                         )
        self.assertEqual(Follow.objects.count(), 0)
        response = self.client.get(url)
        self.assertEqual(len(response.context['page'].object_list), 0)

    
    def test_follow_view(self):
        text = 'testtesttest'
        url = reverse('follow_index')
        Post.objects.create(text=text, author=self.user1,
                                        group=self.group)
        self.client.post(reverse('profile_follow',
                                 args=[self.user1]),
                         {'author': self.user1,
                          'user': self.user})
        self.check_url(url=url, text=text,
                       author=self.user1, group=self.group)


    def test_fake_image_upload(self):
        err='Загрузите правильное изображение. Файл, который вы загрузили, поврежден или не является изображением.'
        not_image = SimpleUploadedFile("test.txt", b"file_content")
        text = 'testtesttest'
        response = self.client.post(reverse('new_post'),
                                        {'text': text,
                                        'image': not_image})
        self.assertFormError(response, 'form', 'image',err)

    @override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}})
    def test_true_image_upload(self):
        image=self.get_image_file()
        text = 'testtesttest1111'
        response = self.client.post(reverse('new_post'),
                                    {'text': text,
                                    'group': self.group.id,
                                    'image': image})
        urls = [
            reverse("index"),
            reverse("profile", args=[self.user.username]),
            reverse('post', args=[self.user, 1]),
            reverse("groups", args=[self.group.slug]),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertContains(response, '<img')


    def test_add_comment(self):
        text = 'test'
        post = Post.objects.create(text=text,
                                   author=self.user,
                                    )
        self.client.post(reverse('add_comment',
                                 args=[post.author,
                                       post.id]),
                         {'author': self.user,
                          'text': text,
                          'post' : post.id})
        comment = post.comments.first()
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.text, text)
    

    def test_not_auth_add_comment(self):
        #немного не понял зачем эта проверка? 
        #за запрет комментариев без авторизации ведь отвечает login_required
        text = 'test'
        post = Post.objects.create(text=text,
                                   author=self.user,
                                    )
        self.client_not_authorized.post(reverse('add_comment',
                                 args=[post.author,
                                       post.id]),
                         {'text': text,
                          'post' : post.id})
        self.assertEqual(Comment.objects.count(), 0)
