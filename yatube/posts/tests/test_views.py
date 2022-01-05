# posts/tests/test_views.py
import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Follow
from yatube.settings import COUNT_PAGINATOR_PAGE


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create_user(
            username='test_user_1'
        )
        cls.user_2 = User.objects.create_user(
            username='test_user_2'
        )
        cls.user_for_3_task = User.objects.create_user(
            username='user_for_3_task'
        )
        cls.group = Group.objects.create(
            slug='test_slug',
            title='1 -Тестовая группа',
            description='1 - Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            slug='2_test_slug',
            title='2 - Тестовая группа',
            description='2- Тестовое описание',
        )
        cls.group_3 = Group.objects.create(
            slug='test_task_3',
            title='Проверка для 3-го задания',
            description='Группа для проверки тестов из 3-го задания',
        )
        cls.test_post_count = 30
        cls.test_posts = (
            Post(
                text=f'№{i} Test нового поста',
                author=(
                    PostPagesTests.user_1 if i % 2 else PostPagesTests.user_2
                ),
                group=(
                    PostPagesTests.group if i % 2 else PostPagesTests.group_2
                ),
            ) for i in range(PostPagesTests.test_post_count)
        )
        Post.objects.bulk_create(PostPagesTests.test_posts)

        from django.core.files.uploadedfile import SimpleUploadedFile
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=PostPagesTests.small_gif,
            content_type='image/gif'
        )

        cls.test_post_for_task_3 = Post.objects.create(
            text='Пост для проверки 3-го задания',
            author=PostPagesTests.user_for_3_task,
            group=PostPagesTests.group_3,
            image=PostPagesTests.uploaded
        )

    def setUp(self):
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:main'),
            'posts/group_list.html': (
                reverse(
                    'posts:group_list',
                    kwargs={'slug': PostPagesTests.group.slug}
                )
            ),
            'posts/profile.html': (
                reverse(
                    'posts:profile',
                    kwargs={'username': PostPagesTests.user_1}
                )
            ),
            'posts/post_detail.html': (
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': PostPagesTests.group.id}
                )
            ),
            'posts/create_post.html': (
                reverse('posts:post_create'),
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': PostPagesTests.group.id}
                )
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            if isinstance(reverse_name, tuple):
                for item in reverse_name:
                    response = self.authorized_client.get(item)
                    self.assertTemplateUsed(response, template)
            else:
                with self.subTest(reverse_name=reverse_name):
                    response = self.authorized_client.get(reverse_name)
                    self.assertTemplateUsed(response, template)

    def test_index_correct_post_paginator(self):
        response = self.authorized_client.get(reverse('posts:main'))
        self.assertEqual(
            response.context['object_list'].count(),
            COUNT_PAGINATOR_PAGE
        )

    def test_group_list_correct_group_and_paginator(self):
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group_2.slug}
            )
        )
        self.assertEqual(
            response.context['object_list'][0].group,
            PostPagesTests.group_2
        )
        self.assertEqual(
            len(response.context['object_list']),
            COUNT_PAGINATOR_PAGE
        )

    def test_profile_list_correct_user_and_paginator(self):
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': PostPagesTests.user_2})
        )
        self.assertEqual(
            response.context['object_list'][0].author.username,
            str(PostPagesTests.user_2)
        )
        self.assertEqual(
            response.context['object_list'].count(),
            COUNT_PAGINATOR_PAGE
        )

    def test_post_detail_correct_post_list_is_1(self):
        post_expected = Post.objects.all()[0]
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post_expected.id})
        )
        self.assertEqual(response.context['post'], post_expected)

    def test_post_create_and_edit_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        post_expected = Post.objects.all()[0]
        response_create = self.authorized_client.get(
            reverse('posts:post_create')
        )
        response_edit = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post_expected.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        self.assertEqual(response_edit.context['post'], post_expected)

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field_creat = (
                    response_create.context.get('form').fields.get(value)
                )
                form_field_edit = (
                    response_edit.context.get('form').fields.get(value)
                )
                if response_create.context['is_edit']:
                    self.assertIsInstance(form_field_edit, expected)
                self.assertIsInstance(form_field_creat, expected)

    def test_post_with_group_correct_view(self):
        page_list = (
            self.authorized_client.get(reverse(
                'posts:main'
            )),
            self.authorized_client.get(reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.test_post_for_task_3.group.slug}
            )),
            self.authorized_client.get(reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user_for_3_task}
            )),
        )

        for response in page_list:
            self.assertTrue(PostPagesTests.test_post_for_task_3 in (
                response.context['object_list']
            ))

        self.assertFalse(
            PostPagesTests.test_post_for_task_3 in (
                self.authorized_client.get(reverse(
                    'posts:group_list',
                    kwargs={'slug': PostPagesTests.group.slug}
                )).context['object_list']
            )
        )

    def test_pages_show_correct_context_image(self):
        """
        Шаблоны index group_list profile post_detail при выводе
        поста с картинкой изображение передаётся c контекстом.
        """
        response_list = (
            self.authorized_client.get(reverse(
                'posts:main'
            )),
            self.authorized_client.get(reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.test_post_for_task_3.group.slug}
            )),
            self.authorized_client.get(reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user_for_3_task}
            )),
            self.authorized_client.get(reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.test_post_for_task_3.id}
            )),
        )

        for response in response_list:
            if response.context.get('object_list'):
                self.assertTrue(response.context['object_list'][0].image)
            else:
                self.assertTrue(response.context['post'].image)

    def test_pages_show_correct_context_comments(self):
        """
        Шаблоны post_detail выводит коментарии
        """
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.test_post_for_task_3.id}
            )
        )
        self.assertTrue(response.context['post'].comment)

    # Проверка работы кэш
    def test_pages_index_cache_reloaded(self):
        """
        Шаблоны posts_index сохраняет список записей в кеше
        """
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        # Данные для тестового поста для проверки кеширования
        data_for_create_post = {
            'text': 'Кеш - Пост для проверки работы кеш',
        }
        # Создаем пост
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=data_for_create_post
        )
        # Проверяем, увеличилось ли число постов в БД
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что пост не успел отобразиться на главной странице
        response = self.guest_client.get(reverse('posts:main'))
        self.assertEqual(
            response.content.decode().find(data_for_create_post['text']),
            -1
        )

    # Авторизованный пользователь может подписываться на других
    def test_authorized_client_can_subscribe_and_unsubscribe(self):
        """
        Обработчик ProfileFollow создает запись на автора
        если клиент авторизован
        """
        response = self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostPagesTests.user_1.username}
            )
        )
        # Проверяем создалась ли запись
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=PostPagesTests.user_1).exists()
        )
        # Проверяем редирект
        self.assertRedirects(
            response,
            reverse('posts:follow_index')
        )

    # Авторизованный пользователь может отписываться
    def test_authorized_client_can_unsubscribe(self):
        """
        Обработчик ProfileUnfollow удаляет запись на автора
        если клиент авторизован
        """
        # Подсчитаем количество записей в Follow
        follow_count = Follow.objects.count()
        # Создаем подписку
        response = self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostPagesTests.user_2.username}
            )
        )
        # Проверяем что количество записей увеличилось
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        # Отписываемся от атора
        response = self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': PostPagesTests.user_2.username}
            )
        )
        # Проверяем что количество записей уменьшилось
        self.assertEqual(Follow.objects.count(), follow_count)
        # Проверяем что удалена именно наша подписка
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=PostPagesTests.user_2).exists()
        )
        # Проверяем редирект
        self.assertRedirects(
            response,
            reverse('posts:follow_index')
        )

    # Проверяем что не авторизованный клиент не может подписываться
    def test_guest_client_can_not_subscribe(self):
        """
        Обработчик ProfileFollow не обрабатывает запросы
        если клиент не авторизован
        """
        # Подсчитаем количество записей в Follow
        follow_count = Follow.objects.count()
        # Пробуем создать запись не авторизованным пользователем
        response = self.guest_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostPagesTests.user_2.username}
            )
        )
        # Проверяем что запись не создалась
        self.assertEqual(Follow.objects.count(), follow_count)
        # Проверяем редирект
        self.assertRedirects(
            response,
            reverse('users:login')
            + f'?next=/profile/{PostPagesTests.user_2.username}/follow/'
        )

    # Новая запись появляется в ленте только у подписчиков
    def test_new_post_see_only_subscribers(self):
        """
        Обработчик FollowIndex показывает список постьов
        на которые подписан пользователь
        """
        # подписываемся на автора
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostPagesTests.user_1.username}
            )
        )
        # создаем новую запись автором на которого подписались
        new_post_user_1 = Post.objects.create(
            text='Для ленты подписчиков проверка',
            author=PostPagesTests.user_1
        )
        # получаем все посты автора на которого подписались из базы
        following_posts = Post.objects.filter(author=PostPagesTests.user_1)
        # заходим на страницу подписок автора
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        # костыль для обхода paginator объединяем все посты с 1 и 2 страницы
        response_post_list = (
            response.context['paginator'].page(1).object_list
            | response.context['paginator'].page(2).object_list
        )
        # проверяем что списки постов из базы и со страницы одинаковые
        self.assertQuerysetEqual(
            following_posts,
            response_post_list,
            transform=lambda x: x)

        # проверяем что запись не появилась в ленте у неподписанного
        # пользователя создаем нового клиента
        new_follower = User.objects.create_user(username='NewFollower')
        authorized_client = Client()
        authorized_client.force_login(new_follower)
        # подписываемся на другого автора
        authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostPagesTests.user_2.username}
            )
        )
        # получаем все посты автора user_2
        response = authorized_client.get(
            reverse('posts:follow_index')
        )
        response_post_list = (
            response.context['paginator'].page(1).object_list
            | response.context['paginator'].page(2).object_list
        )
        # проверяем что post автора user_1 не отображается
        # в списке не подписанного на него пользователя
        self.assertFalse(new_post_user_1 in response_post_list)
