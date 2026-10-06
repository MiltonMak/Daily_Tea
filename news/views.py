"""Views for authentication, articles, newsletters, and publisher management."""

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group, Permission
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from .forms import (
    ArticleForm,
    NewsletterForm,
    PublisherForm,
    RegistrationForm,
    SubscriptionForm,
)

from .models import Article, Newsletter, Publisher, User

from .services import (
    notify_article_subscribers,
    post_approved_article,
)

# Create your views here.


def register(request):
    """Register a new Reader or Journalist."""

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            group_name = user.role.capitalize()

            permissions = {
                "reader": [
                    "view_article",
                    "view_newsletter",
                ],
                "journalist": [
                    "view_article",
                    "add_article",
                    "change_article",
                    "delete_article",
                    "view_newsletter",
                    "add_newsletter",
                    "change_newsletter",
                    "delete_newsletter",
                ],
                "editor": [
                    "view_article",
                    "change_article",
                    "delete_article",
                    "approve_article",
                    "view_newsletter",
                    "add_newsletter",
                    "change_newsletter",
                    "delete_newsletter",
                ],
            }

            group, created = Group.objects.get_or_create(
                name=group_name
            )

            group.permissions.clear()

            for codename in permissions[user.role]:
                permission = Permission.objects.get(
                    codename=codename,
                    content_type__app_label="news",
                )
                group.permissions.add(permission)

            user.groups.clear()
            user.groups.add(group)

            user.clear_invalid_subscriptions()

            login(request, user)

            return redirect("home")
    else:
        form = RegistrationForm()

    return render(
        request,
        "news/register.html",
        {"form": form},
    )


def login_view(request):
    """Authenticate an existing Daily Tea user."""

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = AuthenticationForm(
            request,
            data=request.POST,
        )

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            return redirect("home")
    else:
        form = AuthenticationForm()

    return render(
        request,
        "news/login.html",
        {"form": form},
    )


@login_required
def logout_view(request):
    """Log the current user out."""

    logout(request)

    return redirect("home")


@login_required
def home(request):
    """Display the Daily Tea home page."""

    articles = Article.objects.filter(
        approved=True
    ).order_by("-created_at")[:6]

    return render(
        request,
        "news/home.html",
        {"articles": articles},
    )


@login_required
def article_list(request):
    """Display approved articles to readers."""

    articles = Article.objects.filter(
        approved=True
    ).select_related(
        "author",
        "publisher",
    ).order_by("-created_at")

    return render(
        request,
        "news/article_list.html",
        {"articles": articles},
    )


@login_required
def article_detail(request, pk):
    """Display a single approved article."""

    article = get_object_or_404(
        Article,
        pk=pk,
        approved=True,
    )

    return render(
        request,
        "news/article_detail.html",
        {"article": article},
    )


@login_required
def my_articles(request):
    """Display the journalist's articles and dashboard statistics."""

    if request.user.role != "journalist":
        return redirect("home")

    articles = Article.objects.filter(
        author=request.user
    ).select_related(
        "publisher",
    ).order_by("-created_at")

    total_articles = articles.count()

    approved_articles = articles.filter(
        approved=True
    ).count()

    pending_articles = articles.filter(
        approved=False,
        publisher__isnull=False,
    ).count()

    return render(
        request,
        "news/my_articles.html",
        {
            "articles": articles,
            "total_articles": total_articles,
            "approved_articles": approved_articles,
            "pending_articles": pending_articles,
        },
    )


@login_required
def create_article(request):
    """Allow journalists to create articles."""

    if request.user.role != "journalist":
        return redirect("home")

    if not request.user.has_perm("news.add_article"):
        return redirect("home")

    if request.method == "POST":
        form = ArticleForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():
            article = form.save(commit=False)

            article.author = request.user
            article.approved = False

            article.save()

            return redirect("my_articles")
    else:
        form = ArticleForm(
            user=request.user,
        )

    return render(
        request,
        "news/article_form.html",
        {
            "form": form,
            "page_title": "Create Article",
            "button_text": "Submit Article",
        },
    )


@login_required
def edit_article(request, pk):
    """Allow journalists to edit their own articles."""

    if request.user.role != "journalist":
        return redirect("home")

    if not request.user.has_perm("news.change_article"):
        return redirect("home")

    article = get_object_or_404(
        Article,
        pk=pk,
        author=request.user,
    )

    if request.method == "POST":
        form = ArticleForm(
            request.POST,
            instance=article,
            user=request.user,
        )

        if form.is_valid():
            article = form.save(commit=False)

            # Editing an article sends it back for review.
            article.approved = False

            article.save()

            return redirect("my_articles")
    else:
        form = ArticleForm(
            instance=article,
            user=request.user,
        )

    return render(
        request,
        "news/article_form.html",
        {
            "form": form,
            "page_title": "Edit Article",
            "button_text": "Update Article",
        },
    )


@login_required
def publish_independent_article(request, pk):
    """Allow journalists to publish their own independent articles."""

    if request.user.role != "journalist":
        return redirect("home")

    if not request.user.has_perm("news.change_article"):
        return redirect("home")

    article = get_object_or_404(
        Article,
        pk=pk,
        author=request.user,
        publisher__isnull=True,
        approved=False,
    )

    if request.method == "POST":
        article.approved = True
        article.save(update_fields=["approved"])

        notify_article_subscribers(article)
        post_approved_article(article)

        return redirect("my_articles")

    return render(
        request,
        "news/publish_article_confirm.html",
        {
            "article": article,
        },
    )


@login_required
def delete_article(request, pk):
    """Allow journalists to delete their own articles."""

    if request.user.role != "journalist":
        return redirect("home")

    if not request.user.has_perm("news.delete_article"):
        return redirect("home")

    article = get_object_or_404(
        Article,
        pk=pk,
        author=request.user,
    )

    if request.method == "POST":
        article.delete()

        return redirect("my_articles")

    return render(
        request,
        "news/article_confirm_delete.html",
        {
            "article": article,
        },
    )


@login_required
def editor_dashboard(request):
    """Display articles waiting for editorial approval."""

    if request.user.role != "editor":
        return redirect("home")

    if not request.user.has_perm("news.approve_article"):
        return redirect("home")

    pending_articles = Article.objects.filter(
        approved=False,
        publisher__isnull=False,
    ).select_related(
        "author",
        "publisher",
    ).order_by("-created_at")

    approved_articles = Article.objects.filter(
        approved=True
    ).select_related(
        "author",
        "publisher",
    ).order_by("-created_at")

    return render(
        request,
        "news/editor_dashboard.html",
        {
            "pending_articles": pending_articles,
            "approved_articles": approved_articles,
        },
    )


@login_required
def review_article(request, pk):
    """Allow an editor to review a pending article."""

    if request.user.role != "editor":
        return redirect("home")

    if not request.user.has_perm("news.approve_article"):
        return redirect("home")

    article = get_object_or_404(
        Article.objects.select_related(
            "author",
            "publisher",
        ),
        pk=pk,
        approved=False,
    )

    return render(
        request,
        "news/review_article.html",
        {"article": article},
    )


@login_required
def approve_article(request, pk):
    """Allow editors to approve pending articles."""

    if request.user.role != "editor":
        return redirect("home")

    if not request.user.has_perm("news.approve_article"):
        return redirect("home")

    article = get_object_or_404(
        Article,
        pk=pk,
        approved=False,
    )

    if request.method == "POST":
        article.approved = True
        article.save(update_fields=["approved"])

        notify_article_subscribers(article)
        post_approved_article(article)

        return redirect("editor_dashboard")

    return redirect(
        "review_article",
        pk=article.pk,
    )


@login_required
def editor_edit_article(request, pk):
    """Allow editors to edit any article."""

    if request.user.role != "editor":
        return redirect("home")

    if not request.user.has_perm("news.change_article"):
        return redirect("home")

    article = get_object_or_404(
        Article,
        pk=pk,
    )

    if request.method == "POST":
        form = ArticleForm(
            request.POST,
            instance=article,
        )

        if form.is_valid():
            form.save()

            return redirect("editor_dashboard")
    else:
        form = ArticleForm(
            instance=article,
        )

    return render(
        request,
        "news/article_form.html",
        {
            "form": form,
            "page_title": "Edit Article",
            "button_text": "Save Changes",
        },
    )


@login_required
def editor_delete_article(request, pk):
    """Allow editors to delete any article."""

    if request.user.role != "editor":
        return redirect("home")

    if not request.user.has_perm("news.delete_article"):
        return redirect("home")

    article = get_object_or_404(
        Article,
        pk=pk,
    )

    if request.method == "POST":
        article.delete()

        return redirect("editor_dashboard")

    return render(
        request,
        "news/article_confirm_delete.html",
        {
            "article": article,
            "editor_delete": True,
        },
    )


@login_required
def newsletter_list(request):
    """Display published newsletters."""

    newsletters = Newsletter.objects.select_related(
        "author",
    ).prefetch_related(
        "articles",
    ).order_by("-created_at")

    return render(
        request,
        "news/newsletter_list.html",
        {
            "newsletters": newsletters,
        },
    )


@login_required
def newsletter_detail(request, pk):
    """Display a single newsletter."""

    newsletter = get_object_or_404(
        Newsletter.objects.select_related(
            "author",
        ).prefetch_related(
            "articles",
        ),
        pk=pk,
    )

    return render(
        request,
        "news/newsletter_detail.html",
        {
            "newsletter": newsletter,
        },
    )


@login_required
def create_newsletter(request):
    """Allow journalists and editors to create newsletters."""

    if request.user.role not in ["journalist", "editor"]:
        return redirect("home")

    if not request.user.has_perm("news.add_newsletter"):
        return redirect("home")

    if request.method == "POST":
        form = NewsletterForm(request.POST)

        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()
            form.save_m2m()

            return redirect(
                "newsletter_detail",
                pk=newsletter.pk,
            )
    else:
        form = NewsletterForm()

    return render(
        request,
        "news/newsletter_form.html",
        {
            "form": form,
            "page_title": "Create Newsletter",
            "button_text": "Create Newsletter",
        },
    )


@login_required
def edit_newsletter(request, pk):
    """Allow journalists and editors to edit newsletters."""

    if request.user.role not in ["journalist", "editor"]:
        return redirect("home")

    if not request.user.has_perm("news.change_newsletter"):
        return redirect("home")

    newsletter = get_object_or_404(
        Newsletter,
        pk=pk,
    )

    if (
        request.user.role == "journalist"
        and newsletter.author != request.user
    ):
        return redirect("home")

    if request.method == "POST":
        form = NewsletterForm(
            request.POST,
            instance=newsletter,
        )

        if form.is_valid():
            form.save()

            return redirect(
                "newsletter_detail",
                pk=newsletter.pk,
            )
    else:
        form = NewsletterForm(
            instance=newsletter,
        )

    return render(
        request,
        "news/newsletter_form.html",
        {
            "form": form,
            "page_title": "Edit Newsletter",
            "button_text": "Save Changes",
        },
    )


@login_required
def delete_newsletter(request, pk):
    """Allow journalists and editors to delete newsletters."""

    if request.user.role not in ["journalist", "editor"]:
        return redirect("home")

    if not request.user.has_perm("news.delete_newsletter"):
        return redirect("home")

    newsletter = get_object_or_404(
        Newsletter,
        pk=pk,
    )

    if (
        request.user.role == "journalist"
        and newsletter.author != request.user
    ):
        return redirect("home")

    if request.method == "POST":
        newsletter.delete()
        return redirect("newsletter_list")

    return render(
        request,
        "news/newsletter_confirm_delete.html",
        {
            "newsletter": newsletter,
        },
    )


@login_required
def publisher_list(request):
    """Display all publishers to editors."""

    if request.user.role != "editor":
        return redirect("home")

    publishers = Publisher.objects.prefetch_related(
        "editors",
        "journalists",
    ).order_by("name")

    return render(
        request,
        "news/publisher_list.html",
        {"publishers": publishers},
    )


@login_required
def create_publisher(request):
    """Allow editors to create a publisher and assign staff."""

    if request.user.role != "editor":
        return redirect("home")

    if request.method == "POST":
        form = PublisherForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("publisher_list")
    else:
        form = PublisherForm()

    return render(
        request,
        "news/publisher_form.html",
        {
            "form": form,
            "page_title": "Create Publisher",
            "button_text": "Create Publisher",
        },
    )


@login_required
def manage_publisher(request, pk):
    """Allow editors to update a publisher and its assigned staff."""

    if request.user.role != "editor":
        return redirect("home")

    publisher = get_object_or_404(Publisher, pk=pk)

    if request.method == "POST":
        form = PublisherForm(request.POST, instance=publisher)

        if form.is_valid():
            form.save()
            return redirect("publisher_list")
    else:
        form = PublisherForm(instance=publisher)

    return render(
        request,
        "news/publisher_form.html",
        {
            "form": form,
            "page_title": "Manage Publisher",
            "button_text": "Save Changes",
            "publisher": publisher,
        },
    )


@login_required
def subscriptions(request):
    """Allow readers to manage publisher and journalist subscriptions."""
    if request.user.role != "reader":
        return redirect("home")

    if request.method == "POST":
        form = SubscriptionForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Your subscriptions have been saved successfully.",
            )

            return redirect("subscriptions")
    else:
        form = SubscriptionForm(instance=request.user)

    return render(
        request,
        "news/subscriptions.html",
        {
            "form": form,
        },
    )
