from django.test import TestCase

from ..models import Follow, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='user')
        cls.user2 = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user1,
            text='Тестовый пост длинною более 15 символов',
        )
        cls.follow = Follow.objects.create(
            user=cls.user1,
            author=cls.user2,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        field_str = {
            PostModelTest.group: PostModelTest.group.title,
            PostModelTest.post: PostModelTest.post.text[:15],
            PostModelTest.follow: (
                f'Пользователь {PostModelTest.user1.username} '
                f'подписан на автора {PostModelTest.user2.username}'
            ),
        }
        for field, expected_value in field_str.items():
            with self.subTest(field=field):
                self.assertEqual(str(field), expected_value)
