import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache
from django import forms

from ..models import Follow, Post, Group, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='TestUser1')
        cls.user2 = User.objects.create_user(username='TestUser2')
        cls.group1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug1',
            description='Описание тестовой группы 1',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Описание тестовой группы 2',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user1,
            text='Тестовый текст 1',
            group=cls.group1,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(PostsViewTests.user1)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(PostsViewTests.user2)

    def context_unpack(self, first_object):
        context_dict = {
            'author': first_object.author.username,
            'post_text': first_object.text,
            'group_title': first_object.group.title,
            'image': first_object.image,
        }
        self.assertEqual(context_dict['author'],
                         PostsViewTests.post.author.username)
        self.assertEqual(context_dict['post_text'],
                         PostsViewTests.post.text)
        self.assertEqual(context_dict['group_title'],
                         PostsViewTests.post.group.title)
        self.assertEqual(context_dict['image'],
                         PostsViewTests.post.image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            (reverse('posts:main')): 'posts/index.html',
            (reverse('posts:group_posts',
                     kwargs={'slug': 'test-slug1'})): 'posts/group_list.html',
            (reverse('posts:profile',
                     kwargs={'username': 'TestUser1'})): 'posts/profile.html',
            (reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{PostsViewTests.post.pk}'}
            )): ('posts/post_detail.html'),
            (reverse('posts:post_create')): 'posts/create_post.html',
            (reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{PostsViewTests.post.pk}'}
            )): ('posts/create_post.html'),
            ('unknown_address'): 'core/404.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client1.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом"""
        response = self.authorized_client1.get(
            reverse('posts:main'))
        first_object = response.context['page_obj'][0]
        self.context_unpack(first_object)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом"""
        response = self.authorized_client1.get(reverse(
            'posts:group_posts',
            kwargs={'slug': PostsViewTests.post.group.slug}
        ))
        first_object = response.context['page_obj'][0]
        self.context_unpack(first_object)
        group_object = response.context['group']
        self.assertEqual(group_object,
                         PostsViewTests.post.group)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client1.get(reverse(
            'posts:profile',
            kwargs={'username': PostsViewTests.post.author.username}
        ))
        first_object = response.context['page_obj'][0]
        self.context_unpack(first_object)
        author_object = response.context['author']
        posts_count_object = response.context['posts_count']
        self.assertEqual(author_object, PostsViewTests.post.author)
        self.assertEqual(posts_count_object,
                         PostsViewTests.user1.posts.count())

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.authorized_client1.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': PostsViewTests.post.pk}
        ))
        first_object = response.context['post']
        self.context_unpack(first_object)
        posts_count_object = response.context['author_posts']
        self.assertEqual(first_object, PostsViewTests.post)
        self.assertEqual(posts_count_object,
                         PostsViewTests.user1.posts.count())

    def test_post_create_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client1.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client1.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostsViewTests.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context['post'], PostsViewTests.post)
        self.assertEqual(response.context['is_edit'], True)

    def test_new_post_in_index_group_profile(self):
        """Пост отображается на страницах index, group и profile"""
        list_urls = {
            reverse('posts:main'):
            'Пост не добавлен на главную страницу',
            reverse('posts:group_posts',
                    kwargs={'slug': PostsViewTests.group1.slug}):
            'Пост не добавлен на страницу группы',
            reverse('posts:profile',
                    kwargs={
                        'username': PostsViewTests.post.author.username}):
            'Пост не добавлен на страницу профиля',
        }
        for url, url_error in list_urls.items():
            response = self.authorized_client1.get(url)
            test_posts = response.context['page_obj'][0]
            self.assertEqual(PostsViewTests.post, test_posts, url_error)

    def test_new_post_not_in_wrong_group(self):
        """Пост не попал на страницу другой group"""
        response = self.authorized_client1.get(reverse(
            'posts:group_posts',
            kwargs={'slug': PostsViewTests.group2.slug}))
        test_posts = response.context['page_obj']
        self.assertNotIn(PostsViewTests.post,
                         test_posts,
                         'Пост добавлен не в ту группу'
                         )

    def test_index_group_profile_page_contains_right_amount_records(self):
        """Проверка количества постов на первой и второй странице."""
        posts_obj = [Post(
            author=PostsViewTests.user1,
            text=f'Тестовый текст {i}',
            group=PostsViewTests.group1,
        ) for i in range(12)]
        Post.objects.bulk_create(posts_obj)
        list_urls = (
            reverse('posts:main'),
            reverse('posts:group_posts',
                    kwargs={'slug': PostsViewTests.group1.slug}),
            reverse('posts:profile',
                    kwargs={'username': PostsViewTests.user1.username}),
        )
        for url in list_urls:
            with self.subTest(url=url):
                response = self.authorized_client1.get(url)
                self.assertEqual(len(response.context['page_obj']), 10)
        for url in list_urls:
            with self.subTest(url=url):
                response = self.authorized_client1.get(url + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)

    def test_cache_index(self):
        """Проверка работы кэша страницы index."""
        response = self.authorized_client1.get(reverse('posts:main'))
        posts = response.content
        Post.objects.create(
            text='текст временного поста',
            author=PostsViewTests.user1,
        )
        response_old = self.authorized_client1.get(reverse('posts:main'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client1.get(reverse('posts:main'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)

    def test_follow_unfollow(self):
        """Проверка подписок/отписок на автора"""
        self.authorized_client1.get(reverse(
            'posts:profile_follow', kwargs={'username': PostsViewTests.user2}
        ))
        self.assertTrue(
            Follow.objects.filter(
                user=PostsViewTests.user1,
                author=PostsViewTests.user2
            ).exists()
        )
        self.authorized_client1.get(reverse(
            'posts:profile_unfollow', kwargs={'username': PostsViewTests.user2}
        ))
        self.assertFalse(
            Follow.objects.filter(
                user=PostsViewTests.user1,
                author=PostsViewTests.user2
            ).exists()
        )

    def test_post_in_follow(self):
        """Пост есть в ленте подписок и не появляется у тех кто не подписан"""
        self.post1 = Post.objects.create(
            author=PostsViewTests.user2,
            text='Тестовый текст 2',
            group=PostsViewTests.group1,
        )
        Follow.objects.create(user=PostsViewTests.user1,
                              author=PostsViewTests.user2)
        response1 = self.authorized_client1.get(reverse('posts:follow_index'))
        response2 = self.authorized_client2.get(reverse('posts:follow_index'))
        self.assertIn(self.post1, response1.context['page_obj'])
        self.assertNotIn(PostsViewTests.post, response2.context['page_obj'])
