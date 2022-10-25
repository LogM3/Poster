from django.test import TestCase, Client
from http import HTTPStatus
from ..models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='Unknown')
        cls.user_not_author = User.objects.create_user('NotAuthor')

        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user_author
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Описание тестовой группы'
        )

        cls.public_pages = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user_author.username}/':
                'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html'
        }
        cls.private_pages = {
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.pk}/edit/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        cls.follow_pages = [
            f'/profile/{PostsURLTests.user_author.username}/follow/',
            f'/profile/{PostsURLTests.user_author.username}/unfollow/'
        ]

    def setUp(self):
        super().setUp()
        self.guest_client = Client()
        self.logged_client = Client()
        self.logged_client.force_login(self.user_not_author)
        self.author_client = Client()
        self.author_client.force_login(self.user_author)

    def test_pages_availability_guest(self):
        for page in PostsURLTests.public_pages:
            with self.subTest(page=page):
                self.assertEqual(
                    self.guest_client.get(page).status_code,
                    HTTPStatus.OK,
                    f'Страница {page} недоступна!'
                )

    def test_private_pages_for_guest(self):
        for page in PostsURLTests.private_pages:
            with self.subTest(page=page):
                self.assertRedirects(
                    self.guest_client.get(page, follow=True),
                    f'/auth/login/?next={page}',
                    msg_prefix=f'Не произошел редирект с {page}'
                )

    def test_pages_availability_logged_author(self):
        for page in PostsURLTests.private_pages:
            with self.subTest(page=page):
                self.assertEqual(
                    self.author_client.get(page).status_code,
                    HTTPStatus.OK,
                    f'Страница {page} недоступна'
                )

    def test_pages_availability_logged_not_author(self):
        url = f'/posts/{PostsURLTests.post.pk}/edit/'
        self.assertRedirects(
            self.logged_client.get(url, follow=True),
            f'/posts/{PostsURLTests.post.pk}/',
            msg_prefix=('Пользователь, не являющийся автором поста, '
                        'может редактировать этот пост')
        )

    def test_pages_templates(self):
        urls_templates = {
            **PostsURLTests.public_pages,
            **PostsURLTests.private_pages,
        }

        for url, template in urls_templates.items():
            with self.subTest(page=url):
                self.assertTemplateUsed(
                    self.author_client.get(url),
                    template,
                    f'Страница {url} использует неправильный шаблон'
                )

    def test_follow_pages_redirect_for_guest(self):
        for page in PostsURLTests.follow_pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertRedirects(
                    response,
                    f'/auth/login/?next={page}',
                    msg_prefix=f'Не работает редирект на странице {page}'
                )

    def test_follow_pages_redirect(self):
        for page in PostsURLTests.follow_pages:
            with self.subTest(page=page):
                response = self.logged_client.get(page)
                self.assertRedirects(
                    response,
                    f'/profile/{PostsURLTests.user_author.username}/',
                    msg_prefix=f'Не работает редирект со страницы {page}'
                )

    def test_custom_404(self):
        response = self.guest_client.get('/unexisting_page/404/')
        self.assertTemplateUsed(
            response,
            'core/404.html',
            'Страница 404 использует не тот шаблон, который ожидалось'
        )
