from django.urls import path

from rest_framework.authtoken import views as auth_views

from .api_views import (
    ApprovedArticleAPIView,
    ArticleDetailAPIView,
    ArticleListAPIView,
    NewsletterDetailAPIView,
    NewsletterListAPIView,
    SubscribedArticleListAPIView,
)


urlpatterns = [
    path(
        "token/",
        auth_views.obtain_auth_token,
        name="api_token",
    ),
    path(
        "approved/",
        ApprovedArticleAPIView.as_view(),
        name="api_approved_article",
    ),
    path(
        "articles/",
        ArticleListAPIView.as_view(),
        name="api_article_list",
    ),
    path(
        "articles/<int:pk>/",
        ArticleDetailAPIView.as_view(),
        name="api_article_detail",
    ),
    path(
        "articles/subscribed/",
        SubscribedArticleListAPIView.as_view(),
        name="api_subscribed_articles",
    ),
    path(
        "newsletters/",
        NewsletterListAPIView.as_view(),
        name="api_newsletter_list",
    ),
    path(
        "newsletters/<int:pk>/",
        NewsletterDetailAPIView.as_view(),
        name="api_newsletter_detail",
    ),
]
