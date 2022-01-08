# posts/tests/tests_form.py
import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом удалится
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='userTest')
        cls.group = Group.objects.create(
            slug='test_slug',
            title='Тестовая группа',
            description='Тестовое описание группы',
        )
        # Создаем запись в базе данных для проверки сушествующего slug
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=PostFormTests.user,
            group=PostFormTests.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Удаляем директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

        # Создаем не авторизованный клиент
        self.guest_client = Client()

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        # Создаем картинку для тестов
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small_1.gif',
            content=small_gif,
            content_type='posts/small_1.gif'
        )
        form_data_create = {
            'text': '2 - Тестовый текст поста',
            'group': PostFormTests.group.id,
            'image': uploaded,
        }

        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data_create,
            follow=True
        )
        # Проверяем статус ответа
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': PostFormTests.user})
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись и по очередно поля
        new_post = Post.objects.all().first()
        self.assertEqual(form_data_create['text'], new_post.text)
        self.assertEqual(form_data_create['group'], new_post.group.id)
        self.assertEqual(PostFormTests.user, new_post.author)

    def test_delet_post(self):
        """Пользователь может удалить свой пост."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        # Проверяем что пост может удалить только автор
        user_no_author = User.objects.create_user(username='userNoAuthor')
        user_no_author_client = Client()
        user_no_author_client.force_login(user_no_author)
        response = user_no_author_client.post(
            reverse(
                'posts:post_delete',
                kwargs={'post_id': PostFormTests.post.id}
            ),
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        # Удаляем тестовый пост
        response = self.authorized_client.post(
            reverse(
                'posts:post_delete',
                kwargs={'post_id': PostFormTests.post.id}
            ),
            follow=True
        )
        # Проверяем статус ответа
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': PostFormTests.user})
        )
        # Проверяем, удален ли пост
        self.assertEqual(Post.objects.count(), posts_count - 1)

    def test_no_create_post_guest_client(self):
        """
        Не авторизованный клиент не может
        создаеть запись в Post.
        """
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()

        form_data_create_guest = {
            'text': 'Не авторизованый тестовый текст поста',
            'group': PostFormTests.group.id,
        }

        # Проверяем что не авторизованый клиент не может создать пост
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data_create_guest,
            follow=True
        )
        # Проверяем статус ответа
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('users:login')
            + '?next=' + reverse('posts:post_create')
        )
        # Проверяем, что число постов не увеличилось
        self.assertNotEqual(Post.objects.count(), posts_count + 2)
        # Проверяем что пост не создан
        self.assertFalse(
            Post.objects.filter(
                text=form_data_create_guest['text']).exists()
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small_change.gif',
            content=small_gif,
            content_type='image/gif_change'
        )
        form_data_edit = {
            'text': 'Измененный текст тестового поста',
            'group': PostFormTests.group.id,
            'image': uploaded,
        }
        form_data_edit_guest = {
            'text': 'Не авторизованное изменение',
            'group': PostFormTests.group.id,
            'image': uploaded,
        }
        # Проверка для авторизованного пользователя
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormTests.post.id}
            ),
            data=form_data_edit,
            follow=True
        )
        # Проверяем статус ответа
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=[PostFormTests.post.id])
        )
        # Проверяем, что число постов не увеличилось
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверяем, что запись изменилась и по очередно поля
        new_post = Post.objects.get(text=form_data_edit['text'])
        self.assertEqual(form_data_edit['text'], new_post.text)
        self.assertEqual(form_data_edit['group'], new_post.group.id)
        self.assertEqual(PostFormTests.user, new_post.author)

        # Проверяем что не авторизованый клиент не может изменить пост
        response = self.guest_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormTests.post.id}
            ),
            data=form_data_edit_guest,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('users:login')
            + '?next='
            + reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormTests.post.id}
            )
        )
        # Проверяем изменился ли пост
        self.assertNotEqual(
            form_data_edit_guest['text'],
            PostFormTests.post.text)

    def test_create_comments_guest_and_authorized(self):
        """Валидная форма создает запись в Comments."""
        # Подсчитаем количество записей в Comment
        comments_count = Comment.objects.count()
        form_comments_create = {
            'text': 'Новый коментарий',
            'post': PostFormTests.post.id,
            'author': PostFormTests.user,
        }
        # Отправляем POST-запрос авторизованным пользователем
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostFormTests.post.id}
            ),
            data=form_comments_create,
            follow=True
        )
        # Проверяем статус ответа
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostFormTests.post.id}
            )
        )
        # Проверяем, увеличилось ли число коментариев
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        # Проверяем, что создалась запись и проверяем поля
        new_comment = Comment.objects.all().first()
        self.assertEqual(form_comments_create['text'], new_comment.text)
        self.assertEqual(form_comments_create['post'], new_comment.post.id)
        self.assertEqual(PostFormTests.user, new_comment.author)

    def test_no_create_comments_guest_client(self):
        """
        Валидная форма не создает запись в Comments если клиент не авторизован.
        """
        # Подсчитаем количество записей в Comment
        comments_count = Comment.objects.count()

        form_comments_create = {
            'text': 'Новый коментарий не авторизованного клиента',
            'post': PostFormTests.post.id,
            'author': PostFormTests.user,
        }

        # Проверяем что не авторизованый клиент не может создать коментарий
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostFormTests.post.id}
            ),
            data=form_comments_create,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('users:login')
            + '?next='
            + reverse(
                'posts:add_comment',
                kwargs={'post_id': PostFormTests.post.id}
            )
        )
        # Проверяем, что число постов не увеличилось
        self.assertNotEqual(Post.objects.count(), comments_count)
        # Проверяем что пост не создан
        self.assertFalse(
            Post.objects.filter(
                text=form_comments_create['text']).exists()
        )
