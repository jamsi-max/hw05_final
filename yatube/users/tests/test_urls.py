# users/tests/tests_url.py
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(
            username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_users_correct_template_for_guest_client(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html',
            '/auth/password_reset_form/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/1/123qwe/': 'users/password_reset_confirm.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
        }

        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_urls_users_correct_template_authorized_client(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
            '/auth/logout/': 'users/logged_out.html',
        }

        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response_authorized_client = self.authorized_client.get(adress)
                self.assertEqual(
                    response_authorized_client.status_code, HTTPStatus.OK
                )
                self.assertTemplateUsed(response_authorized_client, template)
                if adress != '/auth/logout/':
                    response_guest_user = self.guest_client.get(adress)
                    self.assertEqual(
                        response_guest_user.status_code, HTTPStatus.FOUND
                    )
