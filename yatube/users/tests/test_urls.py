from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus
from ..forms import UserCreationForm


class UsersUrlsTemplatesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()

    def test_signup_page(self):
        url = reverse('users:signup')
        response = UsersUrlsTemplatesTests.client.get(url)

        self.assertTemplateUsed(response, 'users/signup.html')
        self.assertIsInstance(response.context['form'], UserCreationForm)

    def test_reset_pass_page_url(self):
        url = reverse('users:pass_reset')
        response = UsersUrlsTemplatesTests.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
