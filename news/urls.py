from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path(
        "articles/",
        views.article_list,
        name="article_list",
        ),

    path(
        "articles/<int:pk>/",
        views.article_detail,
        name="article_detail",
        ),

    path(
        "my-articles/",
        views.my_articles,
        name="my_articles",
        ),
    path(
        "articles/create/",
        views.create_article,
        name="create_article",
        ),
    path(
        "articles/<int:pk>/edit/",
        views.edit_article,
        name="edit_article",
        ),
    path(
        "articles/<int:pk>/publish/",
        views.publish_independent_article,
        name="publish_independent_article",
        ),
    path(
        "articles/<int:pk>/delete/",
        views.delete_article,
        name="delete_article",
        ),
    path(
        "editor/",
        views.editor_dashboard,
        name="editor_dashboard",
       ),

    path(
        "editor/articles/<int:pk>/",
        views.review_article,
        name="review_article",
        ),

    path(
        "editor/articles/<int:pk>/approve/",
        views.approve_article,
        name="approve_article",
        ),
    path(
        "editor/articles/<int:pk>/edit/",
        views.editor_edit_article,
        name="editor_edit_article",
        ),

    path(
        "editor/articles/<int:pk>/delete/",
        views.editor_delete_article,
        name="editor_delete_article",
        ),
    path(
        "newsletters/",
        views.newsletter_list,
        name="newsletter_list",
        ),

    path(
        "newsletters/<int:pk>/",
        views.newsletter_detail,
        name="newsletter_detail",
        ),
    path(
        "newsletters/create/",
        views.create_newsletter,
        name="create_newsletter",
        ),
    path(
        "newsletters/<int:pk>/edit/",
        views.edit_newsletter,
        name="edit_newsletter",
        ),
    path(
        "newsletters/<int:pk>/delete/",
        views.delete_newsletter,
        name="delete_newsletter",
        ),
    path(
        "publishers/",
        views.publisher_list,
        name="publisher_list",
    ),
    path(
        "publishers/create/",
        views.create_publisher,
        name="create_publisher",
    ),
    path(
        "publishers/<int:pk>/manage/",
        views.manage_publisher,
        name="manage_publisher",
    ),
    path(
        "subscriptions/",
        views.subscriptions,
        name="subscriptions",
    ),
]
