from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse
from django.conf import settings

from .models import Article, Newsletter, Publisher

from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class ArticleWorkflowTests(TestCase):
    """Test the Daily Tea article workflow and permissions."""

    @classmethod
    def setUpTestData(cls):
        """Create users and permissions used by the tests."""

        cls.reader = User.objects.create_user(
            username="test_reader",
            password="TestPass123!",
            role="reader",
        )

        cls.journalist = User.objects.create_user(
            username="test_journalist",
            password="TestPass123!",
            role="journalist",
        )

        cls.other_journalist = User.objects.create_user(
            username="other_journalist",
            password="TestPass123!",
            role="journalist",
        )

        cls.editor = User.objects.create_user(
            username="test_editor",
            password="TestPass123!",
            role="editor",
        )

        add_article = Permission.objects.get(
            codename="add_article",
        )

        change_article = Permission.objects.get(
            codename="change_article",
        )

        delete_article = Permission.objects.get(
            codename="delete_article",
        )

        approve_article = Permission.objects.get(
            codename="approve_article",
        )

        cls.journalist.user_permissions.add(
            add_article,
            change_article,
            delete_article,
        )

        cls.editor.user_permissions.add(
            change_article,
            delete_article,
            approve_article,
        )

        cls.pending_article = Article.objects.create(
            title="Pending Test Article",
            content="This article is waiting for approval.",
            author=cls.journalist,
            approved=False,
        )

        cls.approved_article = Article.objects.create(
            title="Approved Test Article",
            content="This article has been approved.",
            author=cls.journalist,
            approved=True,
        )

        cls.other_article = Article.objects.create(
            title="Other Journalist Article",
            content="This belongs to another journalist.",
            author=cls.other_journalist,
            approved=False,
        )

    def test_journalist_can_create_article(self):
        """A journalist can create a pending article."""

        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse("create_article"),
            {
                "title": "New Test Article",
                "content": "New article content.",
                "publisher": "",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        article = Article.objects.get(
            title="New Test Article"
        )

        self.assertEqual(
            article.author,
            self.journalist,
        )

        self.assertFalse(
            article.approved,
        )

    @patch("news.views.post_approved_article")
    @patch("news.views.notify_article_subscribers")
    def test_journalist_can_publish_own_independent_article(
        self,
        mock_notify,
        mock_post_api,
    ):
        """A journalist can publish their own independent article."""

        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse(
                "publish_independent_article",
                args=[self.pending_article.pk],
            ),
        )

        self.assertRedirects(
            response,
            reverse("my_articles"),
        )

        self.pending_article.refresh_from_db()

        self.assertTrue(
            self.pending_article.approved,
        )

        mock_notify.assert_called_once_with(
            self.pending_article,
        )

        mock_post_api.assert_called_once_with(
            self.pending_article,
        )

    def test_journalist_cannot_publish_another_journalists_article(self):
        """A journalist cannot publish another journalist's article."""

        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse(
                "publish_independent_article",
                args=[self.other_article.pk],
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.other_article.refresh_from_db()

        self.assertFalse(
            self.other_article.approved,
        )

    def test_journalist_cannot_self_publish_publisher_article(self):
        """A journalist cannot self-publish a publisher article."""

        publisher = Publisher.objects.create(
            name="Test Publisher",
            description="Test publisher.",
        )

        publisher.journalists.add(
            self.journalist,
        )

        publisher_article = Article.objects.create(
            title="Publisher Test Article",
            content="This belongs to a publisher.",
            author=self.journalist,
            publisher=publisher,
            approved=False,
        )

        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse(
                "publish_independent_article",
                args=[publisher_article.pk],
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        publisher_article.refresh_from_db()

        self.assertFalse(
            publisher_article.approved,
        )

    def test_reader_cannot_publish_independent_article(self):
        """A reader cannot publish an independent article."""

        self.client.force_login(self.reader)

        response = self.client.post(
            reverse(
                "publish_independent_article",
                args=[self.pending_article.pk],
            ),
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

        self.pending_article.refresh_from_db()

        self.assertFalse(
            self.pending_article.approved,
        )

    def test_reader_cannot_create_article(self):
        """A reader cannot create an article."""

        self.client.force_login(self.reader)

        response = self.client.get(
            reverse("create_article"),
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

    def test_journalist_can_edit_own_article(self):
        """A journalist can edit their own article."""

        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse(
                "edit_article",
                args=[self.approved_article.pk],
            ),
            {
                "title": "Updated Article",
                "content": "Updated article content.",
                "publisher": "",
            },
        )

        self.assertRedirects(
            response,
            reverse("my_articles"),
        )

        self.approved_article.refresh_from_db()

        self.assertEqual(
            self.approved_article.title,
            "Updated Article",
        )

        self.assertFalse(
            self.approved_article.approved,
        )

    def test_journalist_cannot_edit_another_journalists_article(self):
        """A journalist cannot edit another journalist's article."""

        self.client.force_login(self.journalist)

        response = self.client.get(
            reverse(
                "edit_article",
                args=[self.other_article.pk],
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_journalist_can_delete_own_article(self):
        """A journalist can delete their own article."""

        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse(
                "delete_article",
                args=[self.pending_article.pk],
            ),
        )

        self.assertRedirects(
            response,
            reverse("my_articles"),
        )

        self.assertFalse(
            Article.objects.filter(
                pk=self.pending_article.pk
            ).exists()
        )

    def test_reader_cannot_view_pending_article(self):
        """Readers cannot access unapproved articles."""

        self.client.force_login(self.reader)

        response = self.client.get(
            reverse(
                "article_detail",
                args=[self.pending_article.pk],
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_reader_can_view_approved_article(self):
        """Readers can access approved articles."""

        self.client.force_login(self.reader)

        response = self.client.get(
            reverse(
                "article_detail",
                args=[self.approved_article.pk],
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Approved Test Article",
        )

    @patch("news.views.post_approved_article")
    def test_editor_can_approve_article(
        self,
        mock_post_api,
    ):
        """An editor can approve a pending article."""

        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                "approve_article",
                args=[self.pending_article.pk],
            ),
        )

        self.assertRedirects(
            response,
            reverse("editor_dashboard"),
        )

        self.pending_article.refresh_from_db()

        self.assertTrue(
            self.pending_article.approved,
        )

    def test_reader_cannot_approve_article(self):
        """A reader cannot approve an article."""

        self.client.force_login(self.reader)

        response = self.client.post(
            reverse(
                "approve_article",
                args=[self.pending_article.pk],
            ),
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

        self.pending_article.refresh_from_db()

        self.assertFalse(
            self.pending_article.approved,
        )

    def test_editor_can_edit_any_article(self):
        """An editor can edit an article created by a journalist."""

        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                "editor_edit_article",
                args=[self.pending_article.pk],
            ),
            {
                "title": "Editor Updated Article",
                "content": "Updated by the editor.",
                "publisher": "",
            },
        )

        self.assertRedirects(
            response,
            reverse("editor_dashboard"),
        )

        self.pending_article.refresh_from_db()

        self.assertEqual(
            self.pending_article.title,
            "Editor Updated Article",
        )

    def test_editor_can_delete_any_article(self):
        """An editor can delete an article."""

        article_id = self.pending_article.pk

        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                "editor_delete_article",
                args=[article_id],
            ),
        )

        self.assertRedirects(
            response,
            reverse("editor_dashboard"),
        )

        self.assertFalse(
            Article.objects.filter(
                pk=article_id
            ).exists()
        )

    def test_editor_dashboard_excludes_independent_articles(self):
        """The editor dashboard only shows publisher articles
           awaiting review."""

        self.client.force_login(self.editor)

        response = self.client.get(
            reverse("editor_dashboard"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertNotContains(
            response,
            self.pending_article.title,
        )


class ArticleNotificationTests(TestCase):
    """Tests for article subscriber notifications."""

    @classmethod
    def setUpTestData(cls):
        cls.publisher = Publisher.objects.create(
            name="Daily News",
            description="Test publisher",
        )

        cls.journalist = User.objects.create_user(
            username="journalist",
            password="testpass123",
            email="journalist@example.com",
            role="journalist",
            publisher=cls.publisher,
        )

        cls.reader = User.objects.create_user(
            username="reader",
            password="testpass123",
            email="reader@example.com",
            role="reader",
        )

        cls.reader.subscribed_journalists.add(
            cls.journalist
        )

        cls.article = Article.objects.create(
            title="Test Published Article",
            content="This is test content.",
            author=cls.journalist,
            publisher=cls.publisher,
            approved=True,
        )

    @patch("news.services.send_mail")
    def test_subscriber_receives_article_email(
        self,
        mock_send_mail,
    ):
        from .services import notify_article_subscribers

        count = notify_article_subscribers(
            self.article
        )

        self.assertEqual(count, 1)

        mock_send_mail.assert_called_once()

        call_kwargs = mock_send_mail.call_args.kwargs

        self.assertEqual(
            call_kwargs["subject"],
            "New article published: Test Published Article",
        )

        self.assertIn(
            "reader@example.com",
            call_kwargs["recipient_list"],
        )


class NewsletterWorkflowTests(TestCase):
    """Test the Daily Tea newsletter workflow."""

    @classmethod
    def setUpTestData(cls):
        """Create users and newsletter test data."""

        cls.reader = User.objects.create_user(
            username="newsletter_reader",
            password="TestPass123!",
            role="reader",
        )

        cls.journalist = User.objects.create_user(
            username="newsletter_journalist",
            password="TestPass123!",
            role="journalist",
        )

        cls.other_journalist = User.objects.create_user(
            username="newsletter_other_journalist",
            password="TestPass123!",
            role="journalist",
        )

        cls.editor = User.objects.create_user(
            username="newsletter_editor",
            password="TestPass123!",
            role="editor",
        )

        add_newsletter = Permission.objects.get(
            codename="add_newsletter",
        )

        change_newsletter = Permission.objects.get(
            codename="change_newsletter",
        )

        delete_newsletter = Permission.objects.get(
            codename="delete_newsletter",
        )

        cls.journalist.user_permissions.add(
            add_newsletter,
            change_newsletter,
            delete_newsletter,
        )

        cls.editor.user_permissions.add(
            add_newsletter,
            change_newsletter,
            delete_newsletter,
        )

        cls.article = Article.objects.create(
            title="Newsletter Test Article",
            content="Approved article for newsletter testing.",
            author=cls.journalist,
            approved=True,
        )

        cls.other_article = Article.objects.create(
            title="Second Newsletter Article",
            content="Another approved article.",
            author=cls.other_journalist,
            approved=True,
        )

        cls.newsletter = Newsletter.objects.create(
            title="Test Daily Tea Newsletter",
            description="Newsletter used for automated testing.",
            author=cls.journalist,
        )

        cls.newsletter.articles.add(
            cls.article,
        )

    def test_reader_can_view_newsletter_list(self):
        """Readers can view the newsletter list."""

        self.client.force_login(self.reader)

        response = self.client.get(
            reverse("newsletter_list"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Test Daily Tea Newsletter",
        )

    def test_reader_can_view_newsletter_detail(self):
        """Readers can view newsletter details."""

        self.client.force_login(self.reader)

        response = self.client.get(
            reverse(
                "newsletter_detail",
                args=[self.newsletter.pk],
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Test Daily Tea Newsletter",
        )

        self.assertContains(
            response,
            "Newsletter Test Article",
        )

    def test_journalist_can_create_newsletter(self):
        """A journalist can create a newsletter."""

        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse("create_newsletter"),
            {
                "title": "New Test Newsletter",
                "description": "A new newsletter.",
                "articles": [
                    self.article.pk,
                    self.other_article.pk,
                ],
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        newsletter = Newsletter.objects.get(
            title="New Test Newsletter"
        )

        self.assertEqual(
            newsletter.author,
            self.journalist,
        )

        self.assertEqual(
            newsletter.articles.count(),
            2,
        )

    def test_reader_cannot_create_newsletter(self):
        """A reader cannot create newsletters."""

        self.client.force_login(self.reader)

        response = self.client.get(
            reverse("create_newsletter"),
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

    def test_journalist_can_edit_own_newsletter(self):
        """A journalist can edit their own newsletter."""

        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse(
                "edit_newsletter",
                args=[self.newsletter.pk],
            ),
            {
                "title": "Updated Newsletter",
                "description": "Updated description.",
                "articles": [
                    self.article.pk,
                    self.other_article.pk,
                ],
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "newsletter_detail",
                args=[self.newsletter.pk],
            ),
        )

        self.newsletter.refresh_from_db()

        self.assertEqual(
            self.newsletter.title,
            "Updated Newsletter",
        )

        self.assertEqual(
            self.newsletter.articles.count(),
            2,
        )

    def test_journalist_cannot_edit_another_newsletters(self):
        """A journalist cannot edit another journalist's newsletter."""

        other_newsletter = Newsletter.objects.create(
            title="Other Journalist Newsletter",
            description="Owned by another journalist.",
            author=self.other_journalist,
        )

        self.client.force_login(self.journalist)

        response = self.client.get(
            reverse(
                "edit_newsletter",
                args=[other_newsletter.pk],
            ),
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

    def test_editor_can_edit_any_newsletter(self):
        """An editor can edit another user's newsletter."""

        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                "edit_newsletter",
                args=[self.newsletter.pk],
            ),
            {
                "title": "Editor Updated Newsletter",
                "description": "Updated by editor.",
                "articles": [
                    self.article.pk,
                ],
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "newsletter_detail",
                args=[self.newsletter.pk],
            ),
        )

        self.newsletter.refresh_from_db()

        self.assertEqual(
            self.newsletter.title,
            "Editor Updated Newsletter",
        )

    def test_journalist_can_delete_own_newsletter(self):
        """A journalist can delete their own newsletter."""

        newsletter_id = self.newsletter.pk

        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse(
                "delete_newsletter",
                args=[newsletter_id],
            ),
        )

        self.assertRedirects(
            response,
            reverse("newsletter_list"),
        )

        self.assertFalse(
            Newsletter.objects.filter(
                pk=newsletter_id
            ).exists()
        )

    def test_reader_cannot_delete_newsletter(self):
        """A reader cannot delete newsletters."""

        self.client.force_login(self.reader)

        response = self.client.get(
            reverse(
                "delete_newsletter",
                args=[self.newsletter.pk],
            ),
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )


class RegistrationWorkflowTests(TestCase):
    """Test Daily Tea registration and role assignment."""

    @classmethod
    def setUpTestData(cls):
        """Create the groups required for registration tests."""

        Group.objects.create(
            name="Reader",
        )

        Group.objects.create(
            name="Journalist",
        )

        Group.objects.create(
            name="Editor",
        )

    def test_reader_can_register(self):
        """A user can register as a reader."""

        response = self.client.post(
            reverse("register"),
            {
                "username": "new_reader",
                "first_name": "New",
                "last_name": "Reader",
                "email": "reader@example.com",
                "role": "reader",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

        user = User.objects.get(
            username="new_reader",
        )

        self.assertEqual(
            user.role,
            "reader",
        )

        self.assertTrue(
            user.groups.filter(
                name="Reader",
            ).exists()
        )

    def test_journalist_can_register(self):
        """A user can register as a journalist."""

        response = self.client.post(
            reverse("register"),
            {
                "username": "new_journalist",
                "first_name": "New",
                "last_name": "Journalist",
                "email": "journalist@example.com",
                "role": "journalist",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

        user = User.objects.get(
            username="new_journalist",
        )

        self.assertEqual(
            user.role,
            "journalist",
        )

        self.assertTrue(
            user.groups.filter(
                name="Journalist",
            ).exists()
        )

    def test_editor_can_register(self):
        """A user can register as an editor."""

        response = self.client.post(
            reverse("register"),
            {
                "username": "new_editor",
                "first_name": "New",
                "last_name": "Editor",
                "email": "editor@example.com",
                "role": "editor",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

        user = User.objects.get(
            username="new_editor",
        )

        self.assertEqual(
            user.role,
            "editor",
        )

        self.assertTrue(
            user.groups.filter(
                name="Editor",
            ).exists()
        )

    def test_duplicate_email_is_rejected(self):
        """Registration rejects an email address that is already in use."""

        User.objects.create_user(
            username="existing_user",
            email="existing@example.com",
            password="StrongPass123!",
            role="reader",
        )

        response = self.client.post(
            reverse("register"),
            {
                "username": "another_user",
                "first_name": "Another",
                "last_name": "User",
                "email": "existing@example.com",
                "role": "reader",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "A user with this email address already exists.",
        )
        self.assertFalse(
            User.objects.filter(
                username="another_user",
            ).exists()
        )


class AuthenticationWorkflowTests(TestCase):
    """Test Daily Tea authentication behaviour."""

    @classmethod
    def setUpTestData(cls):
        """Create a test user."""

        cls.user = User.objects.create_user(
            username="auth_test_user",
            password="StrongPass123!",
            role="reader",
        )

    def test_login_page_is_accessible(self):
        """The login page is accessible to visitors."""

        response = self.client.get(
            reverse("login"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_valid_user_can_login(self):
        """A user can log in with valid credentials."""

        response = self.client.post(
            reverse("login"),
            {
                "username": "auth_test_user",
                "password": "StrongPass123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

    def test_invalid_password_is_rejected(self):
        """An incorrect password is rejected."""

        response = self.client.post(
            reverse("login"),
            {
                "username": "auth_test_user",
                "password": "WrongPassword123!",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Please enter a correct username and password",
        )

    def test_unknown_user_is_rejected(self):
        """An unknown username cannot log in."""

        response = self.client.post(
            reverse("login"),
            {
                "username": "does_not_exist",
                "password": "StrongPass123!",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Please enter a correct username and password",
        )

    def test_logout_redirects_to_home(self):
        """A logged-in user can log out."""

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("logout"),
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("home"),
        )

    def test_anonymous_user_cannot_access_home(self):
        """Anonymous users are redirected to login."""

        response = self.client.get(
            reverse("home"),
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('home')}",
        )

    def test_anonymous_user_cannot_access_articles(self):
        """Anonymous users cannot access articles."""

        response = self.client.get(
            reverse("article_list"),
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('article_list')}",
        )

    def test_anonymous_user_cannot_access_newsletters(self):
        """Anonymous users cannot access newsletters."""

        response = self.client.get(
            reverse("newsletter_list"),
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('newsletter_list')}",
        )


class ArticleApprovalIntegrationTests(TestCase):
    """Tests for article approval and subscriber notification."""

    @classmethod
    def setUpTestData(cls):
        cls.publisher = Publisher.objects.create(
            name="Daily Tea News",
            description="Test publisher",
        )

        cls.editor = User.objects.create_user(
            username="editor",
            password="testpass123",
            email="editor@example.com",
            role="editor",
        )

        editor_group = Group.objects.create(
            name="Editor",
        )

        approve_permission = Permission.objects.get(
            codename="approve_article",
            content_type__app_label="news",
        )

        editor_group.permissions.add(
            approve_permission
        )

        cls.editor.groups.add(
            editor_group
        )

        cls.journalist = User.objects.create_user(
            username="journalist_approval",
            password="testpass123",
            email="journalist@example.com",
            role="journalist",
            publisher=cls.publisher,
        )

        cls.reader = User.objects.create_user(
            username="reader_approval",
            password="testpass123",
            email="reader@example.com",
            role="reader",
        )

        cls.reader.subscribed_journalists.add(
            cls.journalist
        )

        cls.article = Article.objects.create(
            title="Article Awaiting Approval",
            content="Article content.",
            author=cls.journalist,
            publisher=cls.publisher,
            approved=False,
        )

    @patch("news.views.post_approved_article")
    @patch("news.views.notify_article_subscribers")
    def test_editor_approval_notifies_subscribers(
        self,
        mock_notify,
        mock_post_api,
    ):
        self.client.force_login(self.editor)

        response = self.client.post(
            f"/editor/articles/{self.article.pk}/approve/"
        )

        self.assertRedirects(
            response,
            "/editor/",
        )

        self.article.refresh_from_db()

        self.assertTrue(
            self.article.approved
        )

        mock_notify.assert_called_once_with(
            self.article
        )
        mock_post_api.assert_called_once_with(
            self.article
        )


class ApprovedArticleAPITests(TestCase):
    """Tests for the approved article API endpoint."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="apiuser",
            password="testpass123",
            email="apiuser@example.com",
            role="editor",
        )

        cls.journalist = User.objects.create_user(
            username="api_journalist",
            password="testpass123",
            email="journalist@example.com",
            role="journalist",
        )

        cls.approved_article = Article.objects.create(
            title="Approved API Article",
            content="This article has been approved.",
            author=cls.journalist,
            approved=True,
        )

        cls.pending_article = Article.objects.create(
            title="Pending API Article",
            content="This article is still pending.",
            author=cls.journalist,
            approved=False,
        )

    def setUp(self):
        self.client = APIClient()

    def test_unauthenticated_user_cannot_submit_article(self):
        response = self.client.post(
            "/api/approved/",
            {
                "article_id": self.approved_article.pk,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_authenticated_user_can_submit_approved_article(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.post(
            "/api/approved/",
            {
                "article_id": self.approved_article.pk,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["id"],
            self.approved_article.pk,
        )

        self.assertEqual(
            response.data["title"],
            "Approved API Article",
        )

        self.assertTrue(
            response.data["approved"]
        )

    def test_pending_article_cannot_be_submitted(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.post(
            "/api/approved/",
            {
                "article_id": self.pending_article.pk,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            response.data["error"],
            "Approved article not found.",
        )

    def test_missing_article_id_returns_bad_request(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.post(
            "/api/approved/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["error"],
            "article_id is required.",
        )


class ApprovedArticleServiceTests(TestCase):
    """Tests for posting approved articles to the API."""

    @classmethod
    def setUpTestData(cls):
        cls.journalist = User.objects.create_user(
            username="service_journalist",
            password="testpass123",
            email="service@example.com",
            role="journalist",
        )

        cls.article = Article.objects.create(
            title="Service Test Article",
            content="Testing API integration.",
            author=cls.journalist,
            approved=True,
        )

    @patch("news.services.requests.post")
    def test_approved_article_is_posted_to_api(
        self,
        mock_post,
    ):
        from .services import post_approved_article

        mock_post.return_value.raise_for_status.return_value = None

        result = post_approved_article(
            self.article
        )

        self.assertTrue(result)

        mock_post.assert_called_once_with(
            "http://127.0.0.1:8000/api/approved/",
            json={"article_id": self.article.pk},
            headers={
                "X-Internal-API-Key": settings.DAILY_TEA_INTERNAL_API_KEY,
            },
            timeout=5,
        )


class ArticleListAPITests(TestCase):
    """Tests for the approved article list API."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="article_api_user",
            password="testpass123",
            email="api@example.com",
            role="reader",
        )

        cls.journalist = User.objects.create_user(
            username="article_api_journalist",
            password="testpass123",
            email="journalist@example.com",
            role="journalist",
        )

        cls.approved_article = Article.objects.create(
            title="Published API Article",
            content="This article is approved.",
            author=cls.journalist,
            approved=True,
        )

        cls.pending_article = Article.objects.create(
            title="Pending API Article",
            content="This article is not approved.",
            author=cls.journalist,
            approved=False,
        )

    def setUp(self):
        self.client = APIClient()

    def test_unauthenticated_user_cannot_list_articles(self):
        response = self.client.get(
            "/api/articles/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_authenticated_user_can_list_articles(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            "/api/articles/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["title"],
            "Published API Article",
        )

    def test_pending_articles_are_not_returned(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            "/api/articles/"
        )

        titles = [
            article["title"]
            for article in response.data
        ]

        self.assertIn(
            "Published API Article",
            titles,
        )

        self.assertNotIn(
            "Pending API Article",
            titles,
        )


class ArticleDetailAPITests(TestCase):
    """Tests for the approved article detail API."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="detail_api_user",
            password="testpass123",
            email="detail@example.com",
            role="reader",
        )

        cls.journalist = User.objects.create_user(
            username="detail_api_journalist",
            password="testpass123",
            email="detail_journalist@example.com",
            role="journalist",
        )

        cls.approved_article = Article.objects.create(
            title="Detailed API Article",
            content="This is the detailed article content.",
            author=cls.journalist,
            approved=True,
        )

        cls.pending_article = Article.objects.create(
            title="Pending Detail Article",
            content="This article is still pending.",
            author=cls.journalist,
            approved=False,
        )

    def setUp(self):
        self.client = APIClient()

    def test_unauthenticated_user_cannot_view_article(self):
        response = self.client.get(
            f"/api/articles/{self.approved_article.pk}/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_authenticated_user_can_view_approved_article(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            f"/api/articles/{self.approved_article.pk}/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["id"],
            self.approved_article.pk,
        )

        self.assertEqual(
            response.data["title"],
            "Detailed API Article",
        )

        self.assertTrue(
            response.data["approved"]
        )

    def test_pending_article_returns_404(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            f"/api/articles/{self.pending_article.pk}/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            response.data["error"],
            "Approved article not found.",
        )

    def test_nonexistent_article_returns_404(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            "/api/articles/99999/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )


class ArticleCreateAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.reader = User.objects.create_user(
            username="api_reader",
            password="testpass123",
            role="reader",
        )

        self.editor = User.objects.create_user(
            username="api_editor",
            password="testpass123",
            role="editor",
        )

        self.journalist = User.objects.create_user(
            username="api_journalist",
            password="testpass123",
            role="journalist",
        )

        self.url = "/api/articles/"

    def test_unauthenticated_user_cannot_create_article(self):
        response = self.client.post(
            self.url,
            {
                "title": "Unauthorised Article",
                "content": "This should fail.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_reader_cannot_create_article(self):
        self.client.force_authenticate(user=self.reader)

        response = self.client.post(
            self.url,
            {
                "title": "Reader Article",
                "content": "Readers cannot create articles.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_editor_cannot_create_article(self):
        self.client.force_authenticate(user=self.editor)

        response = self.client.post(
            self.url,
            {
                "title": "Editor Article",
                "content": "Editors cannot create articles.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_journalist_can_create_article(self):
        self.client.force_authenticate(user=self.journalist)

        response = self.client.post(
            self.url,
            {
                "title": "Journalist Article",
                "content": "This article was created through the API.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        article = Article.objects.get(title="Journalist Article")

        self.assertEqual(article.author, self.journalist)
        self.assertFalse(article.approved)

    def test_journalist_cannot_force_article_approval(self):
        self.client.force_authenticate(user=self.journalist)

        response = self.client.post(
            self.url,
            {
                "title": "Attempted Approved Article",
                "content": "The journalist tries to approve this.",
                "approved": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        article = Article.objects.get(
            title="Attempted Approved Article"
        )

        self.assertFalse(article.approved)


class ArticleUpdateAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.publisher = Publisher.objects.create(
            name="Daily Tea Publishing",
        )

        self.other_publisher = Publisher.objects.create(
            name="Other Publishing",
        )

        self.journalist = User.objects.create_user(
            username="update_journalist",
            password="testpass123",
            role="journalist",
            publisher=self.publisher,
        )

        self.other_journalist = User.objects.create_user(
            username="other_journalist",
            password="testpass123",
            role="journalist",
            publisher=self.other_publisher,
        )

        self.editor = User.objects.create_user(
            username="update_editor",
            password="testpass123",
            role="editor",
        )

        self.reader = User.objects.create_user(
            username="update_reader",
            password="testpass123",
            role="reader",
        )

        self.article = Article.objects.create(
            title="Original Article",
            content="Original content.",
            author=self.journalist,
            publisher=self.publisher,
            approved=False,
        )

        self.url = f"/api/articles/{self.article.pk}/"

    def test_unauthenticated_user_cannot_update_article(self):
        response = self.client.put(
            self.url,
            {
                "title": "Updated Title",
                "content": "Updated content.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_reader_cannot_update_article(self):
        self.client.force_authenticate(user=self.reader)

        response = self.client.put(
            self.url,
            {
                "title": "Reader Updated Title",
                "content": "Reader cannot update.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_journalist_can_update_own_article(self):
        self.client.force_authenticate(user=self.journalist)

        response = self.client.put(
            self.url,
            {
                "title": "Updated Article",
                "content": "Updated article content.",
                "publisher": self.publisher.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.article.refresh_from_db()

        self.assertEqual(
            self.article.title,
            "Updated Article",
        )

        self.assertEqual(
            self.article.content,
            "Updated article content.",
        )

        self.assertEqual(
            self.article.author,
            self.journalist,
        )

    def test_journalist_cannot_update_another_journalists_article(self):
        self.client.force_authenticate(user=self.other_journalist)

        response = self.client.put(
            self.url,
            {
                "title": "Hacked Article",
                "content": "This should not be allowed.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        self.article.refresh_from_db()

        self.assertEqual(
            self.article.title,
            "Original Article",
        )

    def test_editor_can_update_any_article(self):
        self.client.force_authenticate(user=self.editor)

        response = self.client.put(
            self.url,
            {
                "title": "Editor Updated Article",
                "content": "Editor updated this article.",
                "publisher": self.publisher.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.article.refresh_from_db()

        self.assertEqual(
            self.article.title,
            "Editor Updated Article",
        )

        self.assertEqual(
            self.article.content,
            "Editor updated this article.",
        )

    def test_journalist_cannot_change_article_publisher(self):
        self.client.force_authenticate(user=self.journalist)

        response = self.client.put(
            self.url,
            {
                "title": "Changed Publisher Attempt",
                "content": "Testing publisher protection.",
                "publisher": self.other_publisher.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        self.article.refresh_from_db()

        self.assertEqual(
            self.article.publisher,
            self.publisher,
        )

    def test_journalist_cannot_approve_article_with_put(self):
        self.client.force_authenticate(user=self.journalist)

        response = self.client.put(
            self.url,
            {
                "title": "Updated Without Approval",
                "content": "Still awaiting editor approval.",
                "publisher": self.publisher.pk,
                "approved": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.article.refresh_from_db()

        self.assertFalse(self.article.approved)


class ArticleDeleteAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.publisher = Publisher.objects.create(
            name="Delete Publishing",
        )

        self.other_publisher = Publisher.objects.create(
            name="Other Delete Publishing",
        )

        self.journalist = User.objects.create_user(
            username="delete_journalist",
            password="testpass123",
            role="journalist",
            publisher=self.publisher,
        )

        self.other_journalist = User.objects.create_user(
            username="other_delete_journalist",
            password="testpass123",
            role="journalist",
            publisher=self.other_publisher,
        )

        self.editor = User.objects.create_user(
            username="delete_editor",
            password="testpass123",
            role="editor",
        )

        self.reader = User.objects.create_user(
            username="delete_reader",
            password="testpass123",
            role="reader",
        )

        self.article = Article.objects.create(
            title="Article To Delete",
            content="This article will be deleted.",
            author=self.journalist,
            publisher=self.publisher,
            approved=False,
        )

        self.url = f"/api/articles/{self.article.pk}/"

    def test_unauthenticated_user_cannot_delete_article(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 401)

        self.assertTrue(
            Article.objects.filter(pk=self.article.pk).exists()
        )

    def test_reader_cannot_delete_article(self):
        self.client.force_authenticate(user=self.reader)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            Article.objects.filter(pk=self.article.pk).exists()
        )

    def test_journalist_can_delete_own_article(self):
        self.client.force_authenticate(user=self.journalist)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 204)

        self.assertFalse(
            Article.objects.filter(pk=self.article.pk).exists()
        )

    def test_journalist_cannot_delete_another_journalists_article(self):
        self.client.force_authenticate(user=self.other_journalist)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            Article.objects.filter(pk=self.article.pk).exists()
        )

    def test_editor_can_delete_any_article(self):
        self.client.force_authenticate(user=self.editor)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 204)

        self.assertFalse(
            Article.objects.filter(pk=self.article.pk).exists()
        )


class SubscribedArticleAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.publisher = Publisher.objects.create(
            name="Subscribed Publisher",
        )

        self.unsubscribed_publisher = Publisher.objects.create(
            name="Unsubscribed Publisher",
        )

        self.journalist = User.objects.create_user(
            username="subscribed_journalist",
            password="testpass123",
            role="journalist",
            publisher=self.publisher,
        )

        self.unsubscribed_journalist = User.objects.create_user(
            username="unsubscribed_journalist",
            password="testpass123",
            role="journalist",
            publisher=self.unsubscribed_publisher,
        )

        self.reader = User.objects.create_user(
            username="subscriber_reader",
            password="testpass123",
            role="reader",
        )

        self.url = "/api/articles/subscribed/"

        # Reader subscribes to the publisher.
        self.reader.subscribed_publishers.add(
            self.publisher
        )

        # Reader subscribes to the journalist.
        self.reader.subscribed_journalists.add(
            self.journalist
        )

        self.publisher_article = Article.objects.create(
            title="Publisher Article",
            content="Article from subscribed publisher.",
            author=self.unsubscribed_journalist,
            publisher=self.publisher,
            approved=True,
        )

        self.journalist_article = Article.objects.create(
            title="Journalist Article",
            content="Article from subscribed journalist.",
            author=self.journalist,
            publisher=None,
            approved=True,
        )

        self.unsubscribed_article = Article.objects.create(
            title="Unsubscribed Article",
            content="Article from an unsubscribed source.",
            author=self.unsubscribed_journalist,
            publisher=self.unsubscribed_publisher,
            approved=True,
        )

        self.unapproved_article = Article.objects.create(
            title="Unapproved Article",
            content="This should not appear.",
            author=self.journalist,
            publisher=self.publisher,
            approved=False,
        )

    def test_unauthenticated_user_cannot_access_subscribed_articles(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_reader_receives_subscribed_publisher_articles(self):
        self.client.force_authenticate(user=self.reader)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        article_ids = [
            article["id"]
            for article in response.data
        ]

        self.assertIn(
            self.publisher_article.id,
            article_ids,
        )

    def test_reader_receives_subscribed_journalist_articles(self):
        self.client.force_authenticate(user=self.reader)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        article_ids = [
            article["id"]
            for article in response.data
        ]

        self.assertIn(
            self.journalist_article.id,
            article_ids,
        )

    def test_unsubscribed_articles_are_not_returned(self):
        self.client.force_authenticate(user=self.reader)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        article_ids = [
            article["id"]
            for article in response.data
        ]

        self.assertNotIn(
            self.unsubscribed_article.id,
            article_ids,
        )

    def test_unapproved_articles_are_not_returned(self):
        self.client.force_authenticate(user=self.reader)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        article_ids = [
            article["id"]
            for article in response.data
        ]

        self.assertNotIn(
            self.unapproved_article.id,
            article_ids,
        )

    def test_reader_with_no_subscriptions_receives_empty_list(self):
        reader_without_subscriptions = User.objects.create_user(
            username="empty_subscriber",
            password="testpass123",
            role="reader",
        )

        self.client.force_authenticate(
            user=reader_without_subscriptions
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])


class TokenAuthenticationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="token_user",
            password="testpass123",
            role="reader",
        )

        self.url = "/api/token/"

    def test_valid_credentials_return_token(self):
        response = self.client.post(
            self.url,
            {
                "username": "token_user",
                "password": "testpass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn("token", response.data)

        self.assertTrue(
            len(response.data["token"]) > 0
        )

    def test_invalid_password_does_not_return_token(self):
        response = self.client.post(
            self.url,
            {
                "username": "token_user",
                "password": "wrongpassword",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.assertNotIn("token", response.data)

    def test_missing_credentials_are_rejected(self):
        response = self.client.post(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.assertNotIn("token", response.data)

    def test_returned_token_can_authenticate_api_request(self):
        token_response = self.client.post(
            self.url,
            {
                "username": "token_user",
                "password": "testpass123",
            },
            format="json",
        )

        self.assertEqual(token_response.status_code, 200)

        token = token_response.data["token"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token}"
        )

        response = self.client.get(
            "/api/articles/"
        )

        self.assertEqual(response.status_code, 200)


class NewsletterListAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.reader = User.objects.create_user(
            username="newsletter_reader",
            password="testpass123",
            role="reader",
        )

        self.journalist = User.objects.create_user(
            username="newsletter_journalist",
            password="testpass123",
            role="journalist",
        )

        self.article = Article.objects.create(
            title="Newsletter Article",
            content="Article included in newsletter.",
            author=self.journalist,
            approved=True,
        )

        self.unapproved_article = Article.objects.create(
            title="Unapproved Newsletter Article",
            content="This should not be included.",
            author=self.journalist,
            approved=False,
        )

        self.newsletter = Newsletter.objects.create(
            title="Daily Tea Weekly",
            description="This week's top stories.",
            author=self.journalist,
        )

        self.newsletter.articles.add(
            self.article,
            self.unapproved_article,
        )

        self.url = "/api/newsletters/"

    def test_unauthenticated_user_cannot_view_newsletters(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_reader_can_view_newsletters(self):
        self.client.force_authenticate(
            user=self.reader
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_journalist_can_view_newsletters(self):
        self.client.force_authenticate(
            user=self.journalist
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_newsletter_data_is_returned(self):
        self.client.force_authenticate(
            user=self.reader
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        newsletter = response.data[0]

        self.assertEqual(
            newsletter["title"],
            "Daily Tea Weekly",
        )

        self.assertEqual(
            newsletter["description"],
            "This week's top stories.",
        )

        self.assertEqual(
            newsletter["author"],
            self.journalist.username,
        )

    def test_newsletter_contains_approved_article(self):
        self.client.force_authenticate(
            user=self.reader
        )

        response = self.client.get(self.url)

        newsletter = response.data[0]

        self.assertIn(
            self.article.id,
            newsletter["articles"],
        )

    def test_newsletter_does_not_return_unapproved_article(self):
        self.client.force_authenticate(
            user=self.reader
        )

        response = self.client.get(self.url)

        newsletter = response.data[0]

        self.assertNotIn(
            self.unapproved_article.id,
            newsletter["articles"],
        )


class NewsletterCreateAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.reader = User.objects.create_user(
            username="newsletter_create_reader",
            password="testpass123",
            role="reader",
        )

        self.journalist = User.objects.create_user(
            username="newsletter_create_journalist",
            password="testpass123",
            role="journalist",
        )

        self.editor = User.objects.create_user(
            username="newsletter_create_editor",
            password="testpass123",
            role="editor",
        )

        self.article = Article.objects.create(
            title="Approved Newsletter Article",
            content="This article is approved.",
            author=self.journalist,
            approved=True,
        )

        self.unapproved_article = Article.objects.create(
            title="Unapproved Article",
            content="This article is not approved.",
            author=self.journalist,
            approved=False,
        )

        self.url = "/api/newsletters/"

    def test_unauthenticated_user_cannot_create_newsletter(self):
        response = self.client.post(
            self.url,
            {
                "title": "Unauthorised Newsletter",
                "description": "Should fail.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_reader_cannot_create_newsletter(self):
        self.client.force_authenticate(
            user=self.reader
        )

        response = self.client.post(
            self.url,
            {
                "title": "Reader Newsletter",
                "description": "Readers cannot create newsletters.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_journalist_can_create_newsletter(self):
        self.client.force_authenticate(
            user=self.journalist
        )

        response = self.client.post(
            self.url,
            {
                "title": "Journalist Newsletter",
                "description": "Created by a journalist.",
                "articles": [self.article.id],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        newsletter = Newsletter.objects.get(
            title="Journalist Newsletter"
        )

        self.assertEqual(
            newsletter.author,
            self.journalist,
        )

        self.assertIn(
            self.article,
            newsletter.articles.all(),
        )

    def test_editor_can_create_newsletter(self):
        self.client.force_authenticate(
            user=self.editor
        )

        response = self.client.post(
            self.url,
            {
                "title": "Editor Newsletter",
                "description": "Created by an editor.",
                "articles": [self.article.id],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        newsletter = Newsletter.objects.get(
            title="Editor Newsletter"
        )

        self.assertEqual(
            newsletter.author,
            self.editor,
        )

    def test_unapproved_article_cannot_be_added_to_newsletter(self):
        self.client.force_authenticate(
            user=self.journalist
        )

        response = self.client.post(
            self.url,
            {
                "title": "Invalid Newsletter",
                "description": "Contains an unapproved article.",
                "articles": [self.unapproved_article.id],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.assertFalse(
            Newsletter.objects.filter(
                title="Invalid Newsletter"
            ).exists()
        )

    def test_client_cannot_choose_newsletter_author(self):
        self.client.force_authenticate(
            user=self.journalist
        )

        response = self.client.post(
            self.url,
            {
                "title": "Protected Author Newsletter",
                "description": "Testing author protection.",
                "author": self.editor.id,
                "articles": [self.article.id],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        newsletter = Newsletter.objects.get(
            title="Protected Author Newsletter"
        )

        self.assertEqual(
            newsletter.author,
            self.journalist,
        )


class NewsletterDetailAPITests(APITestCase):
    def setUp(self):
        self.reader = User.objects.create_user(
            username="newsletter_reader",
            password="password123",
            role="reader",
        )

        self.journalist = User.objects.create_user(
            username="newsletter_journalist",
            password="password123",
            role="journalist",
        )

        self.article_approved = Article.objects.create(
            title="Approved Article",
            content="Approved article content.",
            author=self.journalist,
            approved=True,
        )

        self.article_unapproved = Article.objects.create(
            title="Unapproved Article",
            content="Unapproved article content.",
            author=self.journalist,
            approved=False,
        )

        self.newsletter = Newsletter.objects.create(
            title="Daily Tea Newsletter",
            description="Today's top stories.",
            author=self.journalist,
        )

        self.newsletter.articles.add(
            self.article_approved,
            self.article_unapproved,
        )

        self.url = reverse(
            "api_newsletter_detail",
            kwargs={"pk": self.newsletter.pk},
        )

    def test_unauthenticated_user_cannot_view_newsletter_detail(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_authenticated_user_can_view_newsletter_detail(self):
        self.client.force_authenticate(user=self.reader)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_newsletter_detail_returns_correct_data(self):
        self.client.force_authenticate(user=self.reader)

        response = self.client.get(self.url)

        self.assertEqual(
            response.data["id"],
            self.newsletter.id,
        )
        self.assertEqual(
            response.data["title"],
            "Daily Tea Newsletter",
        )
        self.assertEqual(
            response.data["description"],
            "Today's top stories.",
        )

    def test_newsletter_detail_only_returns_approved_articles(self):
        self.client.force_authenticate(user=self.reader)

        response = self.client.get(self.url)

        self.assertIn(
            self.article_approved.id,
            response.data["articles"],
        )

        self.assertNotIn(
            self.article_unapproved.id,
            response.data["articles"],
        )

    def test_nonexistent_newsletter_returns_404(self):
        self.client.force_authenticate(user=self.reader)

        response = self.client.get(
            reverse(
                "api_newsletter_detail",
                kwargs={"pk": 999999},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_reader_cannot_update_newsletter(self):
        self.client.force_authenticate(user=self.reader)

        response = self.client.put(
            self.url,
            {
                "title": "Updated Newsletter",
                "description": "Updated description.",
                "articles": [self.article_approved.id],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_journalist_can_update_own_newsletter(self):
        self.client.force_authenticate(user=self.journalist)

        response = self.client.put(
            self.url,
            {
                "title": "Updated Newsletter",
                "description": "Updated description.",
                "articles": [self.article_approved.id],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.newsletter.refresh_from_db()

        self.assertEqual(
            self.newsletter.title,
            "Updated Newsletter",
        )

    def test_journalist_cannot_update_another_journalists_newsletter(self):
        another_journalist = User.objects.create_user(
            username="another_journalist",
            password="password123",
            role="journalist",
        )

        another_newsletter = Newsletter.objects.create(
            title="Another Newsletter",
            description="Another description.",
            author=another_journalist,
        )

        self.client.force_authenticate(user=self.journalist)

        response = self.client.put(
            reverse(
                "api_newsletter_detail",
                kwargs={"pk": another_newsletter.pk},
            ),
            {
                "title": "Trying To Change It",
                "description": "Trying to change another newsletter.",
                "articles": [],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_editor_can_update_any_newsletter(self):
        editor = User.objects.create_user(
            username="newsletter_editor",
            password="password123",
            role="editor",
        )

        self.client.force_authenticate(user=editor)

        response = self.client.put(
            self.url,
            {
                "title": "Editor Updated Newsletter",
                "description": "Updated by editor.",
                "articles": [self.article_approved.id],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.newsletter.refresh_from_db()

        self.assertEqual(
            self.newsletter.title,
            "Editor Updated Newsletter",
        )

    def test_update_nonexistent_newsletter_returns_404(self):
        self.client.force_authenticate(user=self.journalist)

        response = self.client.put(
            reverse(
                "api_newsletter_detail",
                kwargs={"pk": 999999},
            ),
            {
                "title": "Does Not Exist",
                "description": "Does not exist.",
                "articles": [],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_reader_cannot_delete_newsletter(self):
        self.client.force_authenticate(user=self.reader)

        response = self.client.delete(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            Newsletter.objects.filter(
                pk=self.newsletter.pk
            ).exists()
        )

    def test_journalist_can_delete_own_newsletter(self):
        self.client.force_authenticate(user=self.journalist)

        response = self.client.delete(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Newsletter.objects.filter(
                pk=self.newsletter.pk
            ).exists()
        )

    def test_journalist_cannot_delete_another_journalists_newsletter(self):
        another_journalist = User.objects.create_user(
            username="delete_another_journalist",
            password="password123",
            role="journalist",
        )

        another_newsletter = Newsletter.objects.create(
            title="Another Newsletter",
            description="Another description.",
            author=another_journalist,
        )

        self.client.force_authenticate(user=self.journalist)

        response = self.client.delete(
            reverse(
                "api_newsletter_detail",
                kwargs={"pk": another_newsletter.pk},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            Newsletter.objects.filter(
                pk=another_newsletter.pk
            ).exists()
        )

    def test_editor_can_delete_any_newsletter(self):
        editor = User.objects.create_user(
            username="delete_newsletter_editor",
            password="password123",
            role="editor",
        )

        self.client.force_authenticate(user=editor)

        response = self.client.delete(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Newsletter.objects.filter(
                pk=self.newsletter.pk
            ).exists()
        )

    def test_delete_nonexistent_newsletter_returns_404(self):
        self.client.force_authenticate(user=self.journalist)

        response = self.client.delete(
            reverse(
                "api_newsletter_detail",
                kwargs={"pk": 999999},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
