from http import HTTPStatus
import pytest
from pytest_django.asserts import assertFormError, assertRedirects

from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


@pytest.mark.django_db
def test_anonymus_user_cant_create_comment(client, id_for_news, form_data):
    url = reverse('news:detail', args=id_for_news)
    response = client.post(url, data=form_data)
    login_url = reverse('users:login')
    redirect_url = f'{login_url}?next={url}'
    assertRedirects(response, redirect_url)
    assert Comment.objects.count() == 0


def test_user_can_create_comment(author_client, id_for_news, form_data):
    url = reverse('news:detail', args=id_for_news)
    response = author_client.post(url, data=form_data)
    assertRedirects(response, url + '#comments')
    assert Comment.objects.count() == 1
    comment = Comment.objects.get()
    assert comment.text == form_data['text']


def test_user_cant_use_bad_words(author_client, id_for_news):
    bad_word_data = {'text': f'Какой-то текст...{BAD_WORDS[0]} Еще текст'}
    url = reverse('news:detail', args=id_for_news)
    response = author_client.post(url, data=bad_word_data)
    assertFormError(response, form='form', field='text', errors=WARNING)
    assert Comment.objects.count() == 0


def test_author_can_edit_comment(
    author_client, id_for_news, comment, form_data
):
    url = reverse('news:edit', args=(comment.id,))
    response = author_client.post(url, data=form_data)
    expected_url = reverse('news:detail', args=id_for_news) + '#comments'
    assertRedirects(response, expected_url)
    comment.refresh_from_db()
    assert comment.text == form_data['text']


def test_user_cant_edit_comment_of_another_user(
    reader_client, comment, form_data
):
    url = reverse('news:edit', args=(comment.id,))
    response = reader_client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment_from_db.text == comment.text


def test_author_can_delete_comment(author_client, id_for_news, comment):
    url = reverse('news:delete', args=(comment.id,))
    response = author_client.post(url)
    expected_url = reverse('news:detail', args=id_for_news) + '#comments'
    assertRedirects(response, expected_url)
    assert Comment.objects.count() == 0


def test_user_cant_delete_comment_of_another_user(reader_client, comment):
    url = reverse('news:delete', args=(comment.id,))
    response = reader_client.post(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1
