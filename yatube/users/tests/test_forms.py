# users/tests/tests_form.py
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом удалится
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class UserFormTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Удаляем директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()

    def test_create_user(self):
        """Валидная форма создает запись в User."""
        # Подсчитаем количество записей в User
        user_count = User.objects.count()
        form_data = {
            'first_name': 'user_test-first_name',
            'last_name': 'user_test-last_name',
            'username': 'user_test-username',
            'email': 'user_test@test.com',
            'password1': '123zxcZXC',
            'password2': '123zxcZXC',
        }
        # Отправляем POST-запрос
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('posts:main')
        )
        # Проверяем, увеличилось ли число пользователей
        self.assertEqual(User.objects.count(), user_count + 1)
        # Проверяем, что создалась запись
        self.assertTrue(
            User.objects.filter(
                username='user_test-username',
            ).exists()
        )
