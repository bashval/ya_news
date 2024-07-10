import pytest
from django.conf import settings
from django.urls import reverse

from news.forms import CommentForm


@pytest.mark.django_db
def test_news_count(client, add_multiple_news):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    news_count = object_list.count()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client, add_multiple_news):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comment_order(client, id_for_news, add_multiple_comments):
    url = reverse('news:detail', args=id_for_news)
    response = client.get(url)
    assert 'news' in response.context
    news = response.context['news']
    comments = news.comment_set.all()
    all_timestapms = [comment.created for comment in comments]
    sorted_timestamps = sorted(all_timestapms)
    assert all_timestapms == sorted_timestamps


def test_authorized_client_has_form(author_client, id_for_news):
    url = reverse('news:detail', args=id_for_news)
    response = author_client.get(url)
    assert 'form' in response.context
    form = response.context['form']
    assert isinstance(form, CommentForm)


@pytest.mark.django_db
def test_anonymus_user_has_no_form(client, id_for_news):
    url = reverse('news:detail', args=id_for_news)
    response = client.get(url)
    assert 'from' not in response.context
