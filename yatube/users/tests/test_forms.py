from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class UsersFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()

    def test_create_user(self):
        users_count = User.objects.count()
        new_user = {
            'first_name': 'Abdl',
            'last_name': 'Gosd',
            'username': 'AbdlGosd',
            'email': 'adhshba@mail.org',
            'password1': '23lk4j432lk',
            'password2': '23lk4j432lk'
        }
        UsersFormsTests.client.post(
            reverse('users:signup'),
            data=new_user,
            follow=True
        )
        self.assertGreater(User.objects.count(), users_count)
