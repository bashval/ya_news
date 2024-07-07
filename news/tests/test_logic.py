from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment, News

User = get_user_model()


class TestCommentCreation(TestCase):
    COMMENT_TEXT = 'Text of comment'

    @classmethod
    def setUpTestData(cls) -> None:
        cls.news = News.objects.create(title='Header', text='News text.')
        cls.url = reverse('news:detail', args=(cls.news.id,))
        cls.user = User.objects.create(username='Mimo Crocodile')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {'text': cls.COMMENT_TEXT}

    def test_anonymus_user_cant_create_comment(self):
        self.client.post(self.url, data=self.form_data)
        comment_count = Comment.objects.count()
        self.assertEqual(comment_count, 0)

    def test_user_can_create_comment(self):
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, f'{self.url}#comments')
        comment_count = Comment.objects.count()
        self.assertEqual(comment_count, 1)
        comment = Comment.objects.get()
        self.assertEqual(comment.text, self.COMMENT_TEXT)
        self.assertEqual(comment.news, self.news)
        self.assertEqual(comment.author, self.user)

    def test_user_cant_use_bad_words(self):
        bad_words_data = {'text': f'Some text...{BAD_WORDS[0]}, another text.'}
        response = self.auth_client.post(self.url, data=bad_words_data)
        self.assertFormError(
            response,
            form='form',
            field='text',
            errors=WARNING
        )
        comment_count = Comment.objects.count()
        self.assertEqual(comment_count, 0)


class TestCommentEditDelete(TestCase):
    COMMENT_TEXT = 'Text of comment.'
    NEW_COMMENT_TEXT = 'Edited text of comment'

    @classmethod
    def setUpTestData(cls) -> None:
        cls.news = News.objects.create(title='Header', text='Text of news.')
        cls.url = reverse('news:detail', args=(cls.news.id,))
        cls.url_to_comments = cls.url + '#comments'
        cls.author = User.objects.create(username='Comment author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Reader')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.comment = Comment.objects.create(
            news=cls.news,
            author=cls.author,
            text=cls.COMMENT_TEXT
        )
        cls.edit_url = reverse('news:edit', args=(cls.comment.id,))
        cls.delete_url = reverse('news:delete', args=(cls.comment.id,))
        cls.form_data = {'text': cls.NEW_COMMENT_TEXT}

    def test_author_can_delete_comment(self):
        response = self.author_client.post(self.delete_url)
        self.assertRedirects(response, self.url_to_comments)
        comment_count = Comment.objects.count()
        self.assertEqual(comment_count, 0)

    def test_user_cant_delete_comment_of_another_user(self):
        response = self.reader_client.post(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        comment_count = Comment.objects.count()
        self.assertEqual(comment_count, 1)

    def test_author_can_edit_comment(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.url_to_comments)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, self.NEW_COMMENT_TEXT)

    def test_user_cant_edit_comment_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, self.COMMENT_TEXT)
