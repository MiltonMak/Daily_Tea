"""Database models for the Daily Tea news application."""
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class Publisher(models.Model):
    """Represents a news organisation or publisher."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    editors = models.ManyToManyField(
        "User",
        blank=True,
        related_name="editor_publishers",
        limit_choices_to={"role": "editor"},
    )

    journalists = models.ManyToManyField(
        "User",
        blank=True,
        related_name="journalist_publishers",
        limit_choices_to={"role": "journalist"},
    )

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Represents a Daily Tea user and their assigned role."""

    ROLE_CHOICES = [
        ("reader", "Reader"),
        ("journalist", "Journalist"),
        ("editor", "Editor"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="reader",
    )

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    subscribed_publishers = models.ManyToManyField(
        Publisher,
        blank=True,
        related_name="subscribed_readers",
    )

    subscribed_journalists = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="journalist_subscribers",
        limit_choices_to={"role": "journalist"},
    )

    def clean(self):
        """Validate user role and publisher relationships."""

        super().clean()

        if self.role == "reader":
            self.publisher = None

    def save(self, *args, **kwargs):
        """Save the user and remove incompatible reader subscriptions."""

        super().save(*args, **kwargs)
        self.clear_invalid_subscriptions()

    def __str__(self):
        return self.username

    def clear_invalid_subscriptions(self):
        """Remove subscriptions from users who are not readers."""

        if self.role != "reader":
            self.subscribed_publishers.clear()
            self.subscribed_journalists.clear()


class Article(models.Model):
    """Represents a news article published on Daily Tea."""

    title = models.CharField(max_length=200)
    content = models.TextField()

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="articles",
    )

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    class Meta:
        permissions = [
            (
                "approve_article",
                "Can approve articles",
            ),
        ]

    def clean(self):
        """Validate article authorship."""

        super().clean()

        if self.author_id is None:
            return

        if self.author.role != "journalist":
            from django.core.exceptions import ValidationError

            raise ValidationError(
                {
                    "author": (
                        "Only journalists can be article authors."
                    )
                }
            )

    def __str__(self):
        return self.title


class Newsletter(models.Model):
    """Represents a Daily Tea newsletter."""

    title = models.CharField(max_length=200)
    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="newsletters",
    )

    articles = models.ManyToManyField(
        Article,
        related_name="newsletters",
        blank=True,
    )

    def __str__(self):
        return self.title
