from django.test import TestCase, Client
from http import HTTPStatus

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='HasNoName')
        cls.user2 = User.objects.create_user(username='HasName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание тестовой группы',
        )
        cls.post = Post.objects.create(
            author=cls.user1,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_author = Client()
        self.authorized_author.force_login(PostURLTests.user1)
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user2)

    def test_unauthorized_url_exists_at_desired_location(self):
        """Страница доступна любому пользователю."""
        url_list = ('/',
                    f'/group/{PostURLTests.group.slug}/',
                    f'/profile/{PostURLTests.post.author}/',
                    f'/posts/{PostURLTests.post.pk}/'
                    )
        for address in url_list:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_url_exists_at_desired_location(self):
        """Страница /posts/1/edit доступна автору."""
        response = self.authorized_author.get(
            f'/posts/{PostURLTests.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_not_author_unautuhorized_post_page(self):
        """Перенаправление гостя и не автора на другие страницы."""
        url_list = {
            self.authorized_client.get(
                f'/posts/{PostURLTests.post.pk}/edit/'
            ): f'/posts/{PostURLTests.post.pk}/',
            self.guest_client.get(
                '/create/', follow=True): '/auth/login/?next=/create/',
            self.guest_client.get(
                f'/posts/{PostURLTests.post.pk}/edit/', follow=True
            ): f'/auth/login/?next=/posts/{PostURLTests.post.pk}/edit/',
        }
        for response, redirect in url_list.items():
            with self.subTest(response=response):
                self.assertRedirects(response, redirect)

    def test_unknown_url_not_exists_at_desired_location(self):
        """Запрос неизвестной страницы возвращает 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.post.author}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{PostURLTests.post.pk}/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_redirect_unautuhorized_post_comment_page(self):
        """Перенаправление гостя при попытке оставить коммент."""
        response = self.guest_client.get(
            f'/posts/{PostURLTests.post.pk}/comment/',
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{PostURLTests.post.pk}/comment/'
        )
