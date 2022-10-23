from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus


class AboutURLTests(TestCase):
    def test_about_pages(self):
        urls = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html'
        }
        client = Client()

        for url, template in urls.items():
            with self.subTest(page=url):
                response = client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK
                )
                self.assertTemplateUsed(response, template)
