import tempfile
import shutil

from django.db.models.fields.files import ImageFieldFile
from django.core.cache import cache
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import datetime
from django import forms
from django.test import TestCase, Client
from django.urls import reverse
from typing import List
from ..models import Post, Group, User, Comment
from ..forms import PostForm


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')

        cls.empty_group = Group.objects.create(
            title='Group2',
            slug='empty_group',
            description='Group without posts'
        )
        cls.group = Group.objects.create(
            title='TestGroup',
            slug='test_group',
            description='Description of Test Group'
        )
        Post.objects.bulk_create([
            Post(
                text='TestPost',
                author=cls.user,
                group=cls.group
            )] * 13
        )

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.client.force_login(self.user)

    def check_posts_fields(self, page_obj: List[Post], exp_text=None):
        for post in page_obj:
            with self.subTest(post=post):
                self.assertIsInstance(
                    post,
                    Post,
                    'Данный объект не является экземпляром класса <Post>'
                )
                self.assertEqual(
                    post.text,
                    exp_text or 'TestPost',
                    'Текст поста не соответствует ожидаемому'
                )
                self.assertEqual(
                    post.author,
                    PostViewsTests.user,
                    'Автор поста не соответствует ожидаемому'
                )
                self.assertEqual(
                    post.group,
                    PostViewsTests.group,
                    'Группа поста не соответствует ожидаемому'
                )
                self.assertEqual(
                    post.pub_date.date(),
                    datetime.now().date(),
                    'Дата создания поста не соответствует ожидаемой'
                )

    def check_post_id_filter(self, post: Post, expected_number: int):
        self.assertEqual(
            post.pk,
            expected_number,
            f'Странице поста {expected_number} передан пост {post.pk}'
        )

    def check_form_fields(self, form: PostForm):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for field, expected in form_fields.items():
            with self.subTest(field=field):
                self.assertIsInstance(form.fields.get(field), expected)

    def test_index_context(self):
        context = self.client.get(
            reverse('posts:index')
        ).context
        self.check_posts_fields(context['page_obj'])

    def test_group_list_context(self):
        context = self.client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostViewsTests.group.slug}
            )
        ).context
        self.check_posts_fields(context['page_obj'])
        self.assertIsNotNone(
            context.get('group'),
            'В контекст не передана группа'
        )

    def test_group_without_posts_context(self):
        page_obj = self.client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostViewsTests.empty_group.slug}
            )
        ).context['page_obj']
        self.assertEqual(len(page_obj), 0)

    def test_profile_context(self):
        context = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostViewsTests.user}
            )
        ).context
        self.check_posts_fields(context['page_obj'])
        self.assertIsNotNone(
            context.get('author'),
            'В контекст не передан автор'
        )

    def test_post_detail_context(self):
        created_post = Post.objects.create(
            text='Another Post',
            author=PostViewsTests.user,
            group=PostViewsTests.group
        )

        post = self.client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': created_post.pk}
            )
        ).context['post']

        self.check_posts_fields([post], post.text)
        self.check_post_id_filter(post, created_post.pk)

    def test_post_edit_context(self):
        exp_post_id = 1
        context = self.client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': Post.objects.get(pk=exp_post_id).pk}
            )
        ).context

        self.check_posts_fields([context['post']])
        self.check_post_id_filter(context['post'], exp_post_id)
        self.assertIsInstance(
            context.get('form'),
            PostForm,
            'В контекст не была передана форма'
        )
        self.check_form_fields(context['form'])
        self.assertEqual(
            context['is_edit'],
            True,
            'В контекст не была передана переменная is_edit'
        )

    def test_post_create_context(self):
        context = self.client.get(
            reverse('posts:post_create')
        ).context

        self.assertIsInstance(
            context.get('form'),
            PostForm,
            'В контекст страницы не передана форма'
        )
        self.check_form_fields(context['form'])

    def test_paginator(self):
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                'slug': PostViewsTests.group.slug
            }),
            reverse('posts:profile', kwargs={
                'username': PostViewsTests.user
            })
        ]
        for url in urls:
            with self.subTest(page=url):
                response = self.client.get(url).context[
                    'page_obj'
                ]
                self.assertEqual(len(response), 10)

                response = self.client.get(
                    url + '?page=2'
                ).context['page_obj']
                self.assertEqual(len(response), 3)

    def test_comment_context(self):
        post = Post.objects.create(
            text='Post with comment',
            author=PostViewsTests.user
        )
        comment = Comment.objects.create(
            text='Test comment',
            post=post,
            author=PostViewsTests.user
        )
        comments = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': post.pk})
        ).context['comments']

        self.assertEqual(comments[0].text, comment.text)


class PostImageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(username='IMGUser')
        cls.group = Group.objects.create(
            title='Group With Images',
            slug='group_with_img',
            description='Just the group with some images'
        )
        cls.client = Client()

        simple_img = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        upload = SimpleUploadedFile(
            name='simple_img.gif',
            content=simple_img,
            content_type='image/gif'
        )
        cls.post_with_img = Post.objects.create(
            text='Post With Image',
            group=cls.group,
            author=cls.user,
            image=upload
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_image_in_context(self):
        urls = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={
                'username': PostImageTests.user
            }),
            reverse('posts:group_list', kwargs={
                'slug': PostImageTests.group.slug
            })
        ]
        for url in urls:
            with self.subTest(url=url):
                context = PostImageTests.client.get(url).context
                self.assertIsInstance(
                    context.get('page_obj')[0].image,
                    ImageFieldFile,
                    'В контексте не было найдено изображения'
                )

        context = PostImageTests.client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': PostImageTests.post_with_img.pk
            })
        ).context
        self.assertIsInstance(
            context.get('post').image,
            ImageFieldFile,
            'В контексте не было найдено изображения'
        )


class PostCacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test user')
        cls.post = Post.objects.create(
            text='Cached Post',
            author=cls.user
        )

    def setUp(self):
        self.client = Client()

    def test_index_cache(self):
        initial_context = self.client.get(reverse('posts:index')).context

        modified_post = Post.objects.get(pk=PostCacheTests.post.pk)
        modified_post.text = 'changed text'

        cached_context = self.client.get(reverse('posts:index')).context
        self.assertEqual(
            initial_context['page_obj'][0],
            cached_context['page_obj'][0]
        )

        cache.clear()
        modified_context = self.client.get(
            reverse('posts:index')).context
        self.assertEqual(modified_context['page_obj'][0], modified_post)


class PostsFollowsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test user')

        cls.author_sub = User.objects.create_user(username='author1')
        cls.author_no_sub = User.objects.create_user(username='author2')

    def setUp(self):
        self.guest_client = Client()
        self.client = Client()
        self.client.force_login(PostsFollowsTests.user)

    def tearDown(self):
        PostsFollowsTests.user.follower.all().delete()

    def follow_as_logged_user(self, username: str) -> None:
        self.client.get(
            reverse(
                'posts:profile_follow',
                kwargs={
                    'username': username}
            )
        )

    def test_anonymous_user_can_follow(self):
        response = self.guest_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={
                    'username': PostsFollowsTests.author_sub.username}),
            follow=True
        )
        self.assertRedirects(
            response,
            (f'/auth/login/?next=/profile/'
             f'{PostsFollowsTests.author_sub.username}/follow'),
            msg_prefix='Не произошел редирект'
        )
        self.assertEqual(
            PostsFollowsTests.author_sub.following.count(),
            0,
            'Анонимный пользователь смог подписаться на автора'
        )

    def test_user_can_follow(self):
        author = PostsFollowsTests.author_sub
        subs = author.following.count()
        self.follow_as_logged_user(author.username)

        self.assertEqual(
            author.following.count(),
            subs + 1,
            'Пользователь не может подписаться на автора'
        )
        self.assertEqual(
            author.following.first().user,
            PostsFollowsTests.user,
            'Созданная запись Follow некорректна'
        )

    def test_user_can_unfollow(self):
        author = PostsFollowsTests.author_sub
        self.follow_as_logged_user(author.username)
        self.client.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': author.username})
        )
        self.assertEqual(
            author.following.count(),
            0,
            'Пользователь не может отписаться от автора'
        )

    def test_follow_context(self):
        post1 = Post.objects.create(
            text='Post from first author',
            author=PostsFollowsTests.author_sub
        )
        post2 = Post.objects.create(
            text='Post from second author',
            author=PostsFollowsTests.author_no_sub,
        )
        self.follow_as_logged_user(PostsFollowsTests.author_sub.username)
        context = self.client.get(reverse('posts:follow_index')).context
        for post in context['page_obj']:
            self.assertNotEqual(
                post,
                post2,
                ('На странице подписок есть запись от автора, '
                 'на которого не подписан пользователь')
            )
            self.assertEqual(
                post,
                post1,
                ('На странице подписок есть запись от автора, '
                 'на которого не подписан пользователь')
            )
