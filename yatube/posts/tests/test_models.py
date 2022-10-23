from django.test import TestCase
from ..models import Post, Group, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='tester')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='TestGroup',
            description='Описание тестовой группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост длиннее 15-ти символов',
            author=cls.user
        )

    def test_post_group_str(self):
        items_exp_values = {
            PostModelTest.post: PostModelTest.post.text[:15],
            PostModelTest.group: PostModelTest.group.title[:15]
        }
        for item, exp_value in items_exp_values.items():
            with self.subTest(item=item):
                self.assertEqual(str(item), exp_value)

    def test_post_verboses(self):
        field_verboses = {
            'text': 'текст',
            'pub_date': 'дата публикации',
            'author': 'автор',
            'group': 'группа'
        }
        post = PostModelTest.post
        for field, verbose in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    verbose,
                    'Неправильный verbose!'
                )
