from django.db.models import Q

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article, Newsletter
from .permissions import InternalAPIKeyPermission

from .serializers import (
    ApprovedArticleSerializer,
    ArticleCreateSerializer,
    ArticleSerializer,
    NewsletterSerializer,
)


class ApprovedArticleAPIView(APIView):
    """Internal endpoint for approved Daily Tea articles."""

    permission_classes = [InternalAPIKeyPermission]

    def post(self, request):
        """Accept an approved article for API processing."""

        article_id = request.data.get("article_id")

        if not article_id:
            return Response(
                {
                    "error": "article_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            article = Article.objects.select_related(
                "author",
                "publisher",
            ).get(
                pk=article_id,
                approved=True,
            )
        except Article.DoesNotExist:
            return Response(
                {
                    "error": "Approved article not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ApprovedArticleSerializer(article)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class ArticleListAPIView(APIView):
    """API endpoint for listing approved articles."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all approved articles."""

        articles = (
            Article.objects.filter(approved=True)
            .select_related("author", "publisher")
            .order_by("-created_at")
        )

        serializer = ArticleSerializer(articles, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        if request.user.role != "journalist":
            return Response(
                {"error": "Only journalists can create articles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ArticleCreateSerializer(data=request.data)

        if serializer.is_valid():
            publisher = serializer.validated_data.get("publisher")

            if publisher and request.user.publisher != publisher:
                return Response(
                    {
                        "error": (
                            "Journalists can only create articles "
                            "for their own publisher."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            article = serializer.save(
                author=request.user,
                approved=False,
            )

            response_serializer = ArticleSerializer(article)

            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class SubscribedArticleListAPIView(APIView):
    """API endpoint for listing approved articles from subscribed
       publishers and journalists."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        articles = (
            Article.objects.filter(
                approved=True
            )
            .filter(
                Q(publisher__in=request.user.subscribed_publishers.all())
                | Q(author__in=request.user.subscribed_journalists.all())
            )
            .select_related("author", "publisher")
            .distinct()
            .order_by("-created_at")
        )

        serializer = ArticleSerializer(articles, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class NewsletterListAPIView(APIView):
    """API endpoint for listing and creating newsletters."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        newsletters = (
            Newsletter.objects
            .select_related("author")
            .prefetch_related("articles")
            .order_by("-created_at")
        )

        serializer = NewsletterSerializer(
            newsletters,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        if request.user.role not in ["journalist", "editor"]:
            return Response(
                {
                    "error": (
                        "Only journalists and editors can "
                        "create newsletters."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = NewsletterSerializer(
            data=request.data
        )

        if serializer.is_valid():
            newsletter = serializer.save(
                author=request.user
            )

            response_serializer = NewsletterSerializer(
                newsletter
            )

            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class NewsletterDetailAPIView(APIView):
    """API endpoint for retrieving, updating, and deleting one newsletter."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            newsletter = (
                Newsletter.objects
                .select_related("author")
                .prefetch_related("articles")
                .get(pk=pk)
            )
        except Newsletter.DoesNotExist:
            return Response(
                {"error": "Newsletter not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = NewsletterSerializer(newsletter)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):
        try:
            newsletter = (
                Newsletter.objects
                .select_related("author")
                .prefetch_related("articles")
                .get(pk=pk)
            )
        except Newsletter.DoesNotExist:
            return Response(
                {"error": "Newsletter not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Readers cannot update newsletters.
        if request.user.role == "reader":
            return Response(
                {"error": "Readers cannot update newsletters."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Journalists can only update their own newsletters.
        if (
            request.user.role == "journalist"
            and newsletter.author != request.user
        ):
            return Response(
                {
                    "error": (
                        "Journalists can only update "
                        "their own newsletters."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Only journalists and editors can update newsletters.
        if request.user.role not in ["journalist", "editor"]:
            return Response(
                {
                    "error": (
                        "You do not have permission "
                        "to update newsletters."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = NewsletterSerializer(
            newsletter,
            data=request.data,
        )

        if serializer.is_valid():
            updated_newsletter = serializer.save()

            return Response(
                NewsletterSerializer(updated_newsletter).data,
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        try:
            newsletter = Newsletter.objects.get(pk=pk)
        except Newsletter.DoesNotExist:
            return Response(
                {"error": "Newsletter not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Readers cannot delete newsletters.
        if request.user.role == "reader":
            return Response(
                {"error": "Readers cannot delete newsletters."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Journalists can only delete their own newsletters.
        if (
            request.user.role == "journalist"
            and newsletter.author != request.user
        ):
            return Response(
                {
                    "error": (
                        "Journalists can only delete "
                        "their own newsletters."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Only journalists and editors can delete newsletters.
        if request.user.role not in ["journalist", "editor"]:
            return Response(
                {
                    "error": (
                        "You do not have permission "
                        "to delete newsletters."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        newsletter.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class ArticleDetailAPIView(APIView):
    """API endpoint for retrieving one approved article."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Return one approved article."""

        try:
            article = (
                Article.objects.select_related("author", "publisher")
                .get(pk=pk, approved=True)
            )
        except Article.DoesNotExist:
            return Response(
                {"error": "Approved article not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ArticleSerializer(article)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):
        try:
            article = Article.objects.select_related(
                "author",
                "publisher",
            ).get(pk=pk)
        except Article.DoesNotExist:
            return Response(
                {"error": "Article not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Readers cannot update articles.
        if request.user.role == "reader":
            return Response(
                {"error": "Readers cannot update articles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Journalists can only update their own articles.
        if (
            request.user.role == "journalist"
            and article.author != request.user
        ):
            return Response(
                {
                    "error": (
                        "Journalists can only update "
                        "their own articles."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Only journalists and editors can update articles.
        if request.user.role not in ["journalist", "editor"]:
            return Response(
                {"error": "You do not have permission to update articles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ArticleCreateSerializer(
            article,
            data=request.data,
        )

        if serializer.is_valid():
            publisher = serializer.validated_data.get(
                "publisher",
                article.publisher,
            )

            # Journalists can only use their own publisher.
            if (
                request.user.role == "journalist"
                and publisher
                and request.user.publisher != publisher
            ):
                return Response(
                    {
                        "error": (
                            "Journalists can only assign "
                            "their own publisher."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            updated_article = serializer.save()

            # Journalists cannot approve articles through PUT.
            if request.user.role == "journalist":
                updated_article.approved = article.approved
                updated_article.save(update_fields=["approved"])

            response_serializer = ArticleSerializer(updated_article)

            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        try:
            article = Article.objects.get(pk=pk)
        except Article.DoesNotExist:
            return Response(
                {"error": "Article not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Readers cannot delete articles.
        if request.user.role == "reader":
            return Response(
                {"error": "Readers cannot delete articles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Journalists can only delete their own articles.
        if (
            request.user.role == "journalist"
            and article.author != request.user
        ):
            return Response(
                {
                    "error": (
                        "Journalists can only delete "
                        "their own articles."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Only journalists and editors can delete articles.
        if request.user.role not in ["journalist", "editor"]:
            return Response(
                {"error": "You do not have permission to delete articles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        article.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )
