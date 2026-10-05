from rest_framework import serializers

from .models import Article, Newsletter, Publisher, User


class ArticleSerializer(serializers.ModelSerializer):
    """Serialize Daily Tea articles."""

    author = serializers.StringRelatedField(
        read_only=True,
    )

    publisher = serializers.StringRelatedField(
        read_only=True,
    )

    class Meta:
        model = Article
        fields = (
            "id",
            "title",
            "content",
            "author",
            "publisher",
            "created_at",
            "approved",
        )

        read_only_fields = (
            "id",
            "author",
            "created_at",
            "approved",
        )


class ArticleCreateSerializer(serializers.ModelSerializer):
    """Serialize Daily Tea articles for creation."""
    publisher = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Article
        fields = (
            "id",
            "title",
            "content",
            "publisher",
            "created_at",
            "approved",
        )
        read_only_fields = (
            "id",
            "created_at",
            "approved",
        )


class ApprovedArticleSerializer(serializers.ModelSerializer):
    """Serialize approved articles for the internal API."""

    author = serializers.StringRelatedField()
    publisher = serializers.StringRelatedField()

    class Meta:
        model = Article
        fields = (
            "id",
            "title",
            "content",
            "author",
            "publisher",
            "created_at",
            "approved",
        )

        read_only_fields = (
            "id",
            "author",
            "publisher",
            "created_at",
            "approved",
        )


class UserSerializer(serializers.ModelSerializer):
    """Serialize Daily Tea users."""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "publisher",
        )

        read_only_fields = (
            "id",
        )


class PublisherSerializer(serializers.ModelSerializer):
    """Serialize Daily Tea publishers."""

    class Meta:
        model = Publisher
        fields = (
            "id",
            "name",
            "description",
            "created_at",
        )

        read_only_fields = (
            "id",
            "created_at",
        )


class NewsletterSerializer(serializers.ModelSerializer):
    """Serialize Daily Tea newsletters."""

    author = serializers.StringRelatedField(read_only=True)

    articles = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Article.objects.filter(approved=True),
        required=False,
    )

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation["articles"] = list(
            instance.articles.filter(approved=True).values_list(
                "id",
                flat=True,
            )
        )

        return representation

    class Meta:
        model = Newsletter
        fields = (
            "id",
            "title",
            "description",
            "created_at",
            "author",
            "articles",
        )
        read_only_fields = (
            "id",
            "created_at",
            "author",
        )
