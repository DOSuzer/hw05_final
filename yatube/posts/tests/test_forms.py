import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Post, Group, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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
        cls.post1 = Post.objects.create(
            author=cls.user1,
            text='Тестовый текст 1',
            group=cls.group1,
            image=uploaded,
        )
        cls.post2 = Post.objects.create(
            author=cls.user2,
            text='Тестовый текст 2',
            group=cls.group1,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(PostFormTests.user1)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(PostFormTests.user2)

    def test_create_post_form(self):
        """Валидная форма создает пост в Post."""
        post_count = Post.objects.count()
        small_gif2 = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=small_gif2,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст 3',
            'group': PostFormTests.group1.id,
            'image': uploaded,
        }
        response = self.authorized_client1.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': PostFormTests.user1.username})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст 3',
                group=PostFormTests.group1.id,
                image='posts/small2.gif'
            ).exists()
        )

    def test_create_post_unauthorized_form(self):
        """Неавторизованный пользователь не создаст пост."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст 3',
            'group': PostFormTests.group1.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), post_count)

    def test_edit_post_form(self):
        """Валидная форма редактирует пост в Post."""
        post_count = Post.objects.count()
        new_text = 'Новый текст поста'
        small_gif3 = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small3.gif',
            content=small_gif3,
            content_type='image/gif'
        )
        response = self.authorized_client2.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormTests.post2.id},
            ),
            data={
                'text': new_text,
                'group': PostFormTests.group2.id,
                'image': uploaded,
            },
            follow=True,
        )
        PostFormTests.post2.refresh_from_db()
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostFormTests.post2.id}
            )
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                id=PostFormTests.post2.id,
                text='Новый текст поста',
                group=PostFormTests.group2.id,
                image='posts/small3.gif'
            ).exists()
        )

    def test_add_comment_form(self):
        """Валидная форма создает коммент к Post."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент 1',
        }
        response = self.authorized_client1.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostFormTests.post1.id},
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostFormTests.post1.id}
            )
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый коммент 1',
                post=PostFormTests.post1.id,
            ).exists()
        )

    def test_add_comment_unauthorized_form(self):
        """Неавторизованный пользователь не создаст коммент."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент 2',
        }
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostFormTests.post1.id},
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{PostFormTests.post1.id}/comment/'
        )
        self.assertEqual(Comment.objects.count(), comment_count)
