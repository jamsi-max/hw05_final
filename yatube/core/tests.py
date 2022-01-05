from http import HTTPStatus

from django.test import Client, TestCase


class ViewTestClass(TestCase):
    @classmethod
    def setUp(self):
        self.client = Client()

    def test_error_page_status_404(self):
        response = self.client.get('/nonexist-page/')
        # Проверяем, что статус ответа сервера - 404
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Проверьте, что используется шаблон core/404.html
        self.assertTemplateUsed(response, 'core/404.html')
