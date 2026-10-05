from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Article, Newsletter, Publisher, User


class RegistrationForm(UserCreationForm):
    """Form used to register new Daily Tea users."""

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """Ensure that the role field has the correct choices
           for registration."""

        self.fields["role"].choices = [
            ("reader", "Reader"),
            ("journalist", "Journalist"),
            ("editor", "Editor"),
        ]

    def clean_email(self):
        """Ensure that email addresses are unique."""

        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "A user with this email address already exists."
            )

        return email

    def clean(self):
        """Validate registration data based on the selected role."""

        cleaned_data = super().clean()

        role = cleaned_data.get("role")

        if role not in ("reader", "journalist", "editor"):
            self.add_error(
                "role",
                "Please select a valid registration role.",
            )

        return cleaned_data


class PublisherForm(forms.ModelForm):
    """Form used by editors to create and manage publishers."""

    class Meta:
        model = Publisher
        fields = (
            "name",
            "description",
            "editors",
            "journalists",
        )
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter publisher name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Describe the publisher...",
                }
            ),
            "editors": forms.SelectMultiple(
                attrs={
                    "class": "form-select",
                    "size": 6,
                }
            ),
            "journalists": forms.SelectMultiple(
                attrs={
                    "class": "form-select",
                    "size": 8,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """Filter editors and journalists to only show
           users with the appropriate roles."""

        self.fields["editors"].queryset = User.objects.filter(
            role="editor"
        ).order_by("username")

        self.fields["journalists"].queryset = User.objects.filter(
            role="journalist"
        ).order_by("username")


class ArticleForm(forms.ModelForm):
    """Form used by journalists to create and edit articles."""

    class Meta:
        model = Article
        fields = (
            "title",
            "content",
            "publisher",
        )

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter article title",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 12,
                    "placeholder": "Write your article here...",
                }
            ),
            "publisher": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        """Filter the publisher field to only show publishers
           that the journalist is assigned to. If the user is not
           a journalist, the publisher field is not required."""

        self.fields["publisher"].required = False

        if user is not None and user.role == "journalist":
            assigned_publishers = Publisher.objects.filter(
                journalists=user
            ).order_by("name")

            self.fields["publisher"].queryset = assigned_publishers


class NewsletterForm(forms.ModelForm):
    """Form used to create and edit newsletters."""

    class Meta:
        model = Newsletter
        fields = (
            "title",
            "description",
            "articles",
        )
        """Ensure that the articles field only shows approved articles
           and is ordered by the most recently created articles first.
        """
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter newsletter title",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Describe this newsletter...",
                }
            ),
            "articles": forms.SelectMultiple(
                attrs={
                    "class": "form-select",
                    "size": 8,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["articles"].queryset = Article.objects.filter(
            approved=True
        ).order_by("-created_at")


class SubscriptionForm(forms.ModelForm):
    """Allow readers to manage publisher and journalist subscriptions."""

    class Meta:
        model = User
        fields = (
            "subscribed_publishers",
            "subscribed_journalists",
        )
        widgets = {
            "subscribed_publishers": forms.CheckboxSelectMultiple(),
            "subscribed_journalists": forms.CheckboxSelectMultiple(),
        }

    """Ensure that the subscription form only shows publishers and journalists
       that the reader can subscribe to, ordered alphabetically by name or
       username.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["subscribed_publishers"].queryset = (
            Publisher.objects.all().order_by("name")
        )

        self.fields["subscribed_journalists"].queryset = (
            User.objects.filter(role="journalist").order_by("username")
        )
