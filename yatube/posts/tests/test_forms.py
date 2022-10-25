import tempfile
import shutil

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from ..models import Post, User, Group

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='TestGroup',
            slug='Group1',
            description='Testing Group'
        )

        image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.upload = SimpleUploadedFile(
            name='image.gif',
            content=image,
            content_type='image/gif'
        )

    def setUp(self):
        super().setUp()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.client = Client()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        posts_total = Post.objects.count()
        payload = {
            'text': 'test post',
            'group': PostsFormsTests.group.pk,
            'image': PostsFormsTests.upload
        }

        self.authorized_client.post(
            reverse('posts:post_create'),
            data=payload,
            follow=True
        )
        self.assertEqual(
            Post.objects.count(),
            posts_total + 1,
            'Новый пост не создался в базе...'
        )

        created_post = Post.objects.first()
        self.assertEqual(created_post.text, payload['text'])
        self.assertEqual(created_post.group.pk, payload['group'])
        self.assertEqual(
            str(created_post.image),
            f'posts/{payload["image"]}'
        )

    def test_edit_post(self):
        second_group = Group.objects.create(
            title='Second TestGroup',
            slug='Group2',
            description='Second Testing Group'
        )
        post = Post.objects.create(
            text='test post',
            author=PostsFormsTests.author,
            group=PostsFormsTests.group,
            image=PostsFormsTests.upload
        )
        payload = {
            'text': 'edited text',
            'group': second_group.pk,
            'image-clear': 'on'
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}),
            data=payload,
            follow=True
        )
        edited_post = Post.objects.first()

        self.assertEqual(
            payload['text'],
            edited_post.text,
            'Текст поста не изменяется...'
        )
        self.assertEqual(
            Group.objects.get(pk=payload['group']),
            edited_post.group,
            'Группа поста не изменяется...'
        )
        self.assertEqual(
            str(edited_post.image),
            '',
            'Изображение поста не удаляется'
        )

    # def test_guest_redirect(self):
    #     posts_total = Post.objects.count()
    #     response = self.client.get(reverse('posts:post_create'),
    #                                follow=True)
    #     self.assertRedirects(
    #         response, '/auth/login/?next=/create/',
    #         msg_prefix='Не работает редирект...'
    #     )
    #     self.assertEqual(
    #         posts_total,
    #         Post.objects.count(),
    #         'Создался новый пост, хотя не должен был...'
    #     )

    # def test_comment_form_redirect(self):
    #     comment_post = Post.objects.create(
    #         text='Post With Comments',
    #         author=PostsFormsTests.author
    #     )
    #     response = self.client.get(
    #         reverse('posts:add_comment', kwargs={
    #                 'post_id': comment_post.pk}),
    #         follow=True
    #     )
    #     self.assertRedirects(
    #         response,
    #         (f'/auth/login/?next=/posts/'
    #          f'{comment_post.pk}/comment/'),
    #         msg_prefix='Не работает редирект...'
    #     )

    def test_comment_form(self):
        comment_post = Post.objects.create(
            text='Post With Comments',
            author=PostsFormsTests.author
        )
        comments_count = comment_post.comments.count()
        payload = {'text': 'Test comment'}
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                    'post_id': comment_post.pk}),
            data=payload
        )

        self.assertEqual(
            comment_post.comments.count(),
            comments_count + 1,
            'У поста в данном тесте должен быть только один комментарий'
        )
        self.assertEqual(
            comment_post.comments.first().text,
            payload['text'],
            'Текст созданного комментария не соответствует ожидаемому'
        )
