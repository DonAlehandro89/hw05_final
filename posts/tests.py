from django.test import TestCase, Client
from .models import Post, Group, User, Follow, Comment
from django.shortcuts import reverse
from django.core.cache import caches, cache
from django.core.cache.utils import make_template_fragment_key


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
        self.post = Post.objects.create(text=text, author=self.user,
                                        group=self.group)
        urls = [
            reverse('post', args=[self.post.author, self.post.id]),
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
        self.post = Post.objects.create(text=text1,
                                        author=self.user,
                                        group=self.group1)
        self.client.post(reverse('post_edit',
                                 args=[self.post.author,
                                       self.post.id]),
                         {'text': text,
                          'group': self.group.id})
        urls = [
            reverse('post', args=[self.post.author, self.post.id]),
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
        text = 'testtesttest'
        self.post = Post.objects.create(text=text, author=self.user1,
                                        group=self.group)
        self.client.post(reverse('profile_follow',
                                 args=[self.user1]),
                         {'author': self.user1,
                          'user': self.user})
        self.assertEqual(Follow.objects.count(), 1)
        follow = Follow.objects.first()
        self.assertEqual(follow.author, self.user1)
        self.assertEqual(follow.user, self.user)
        url = reverse('follow_index')
        self.check_url(url=url, text=text,
                       author=self.user1, group=self.group)
        self.client.post(reverse('profile_unfollow',
                                 args=[self.user1]),
                         {'author': self.user1,
                          'user': self.user})
        self.assertEqual(Follow.objects.count(), 0)
        response = self.client.get(url)
        self.assertEqual(len(response.context['page'].object_list), 0)

    def test_fake_image_upload(self):
            err='Загрузите правильное изображение. Файл, который вы загрузили, поврежден или не является изображением.'
                
            #with open('media/posts/vk.png', 'rb') as img:
            with open('requirements.txt', 'rb') as img:
                text = 'testtesttest'
                response = self.client.post(reverse('new_post'),
                                             {'text': text,
                                            'image': img})
                self.assertFormError(response, 'form', 'image',err)
            #self.assertEqual(Post.objects.count(), 0)


    def test_true_image_upload(self):
        with open('media/posts/vk.png', 'rb') as img:
            text = 'testtesttest1111'
            response = self.client.post(reverse('new_post'),
                                       {'text': text,
                                        'group': self.group.id,
                                        'image': img})
        response = self.client.get(reverse("profile", args=[self.user.username]))
        self.assertContains(response, '<img')
        response = self.client.get(reverse('post', args=[self.user, 1]))
        self.assertContains(response, '<img')
        cache.clear()
        response = self.client.get(reverse("index"))
        self.assertContains(response, '<img')
        response = self.client.get(reverse("groups", args=[self.group.slug]))
        self.assertContains(response, '<img')


