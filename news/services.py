import requests

from django.core.mail import send_mail
from django.conf import settings

from .models import Article


def notify_article_subscribers(article):
    """
    Notify readers who subscribe to the article's journalist
    or publisher.
    """

    if not article.approved:
        return 0

    recipients = set()

    # Readers subscribed to the journalist.
    journalist_subscribers = (
        article.author.journalist_subscribers.filter(
            role="reader"
        )
    )

    for reader in journalist_subscribers:
        if reader.email:
            recipients.add(reader.email)

    # Readers subscribed to the publisher.
    if article.publisher:
        publisher_subscribers = (
            article.publisher.subscribed_readers.filter(
                role="reader"
            )
        )

        for reader in publisher_subscribers:
            if reader.email:
                recipients.add(reader.email)

    if not recipients:
        return 0

    subject = f"New article published: {article.title}"

    message = (
        f"Hello,\n\n"
        f"A new article has been published on Daily Tea.\n\n"
        f"Title: {article.title}\n"
        f"Author: {article.author.get_full_name() or article.author.username}\n\n"
        f"Read it on Daily Tea.\n\n"
        f"Daily Tea\n"
        f"Your daily dose of what's happening."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=None,
        recipient_list=list(recipients),
        fail_silently=False,
    )

    return len(recipients)


def post_approved_article(article):
    if not article.approved:
        return False

    headers = {
        "X-Internal-API-Key": settings.DAILY_TEA_INTERNAL_API_KEY,
    }

    response = requests.post(
        "http://127.0.0.1:8000/api/approved/",
        json={"article_id": article.pk},
        headers=headers,
        timeout=5,
    )

    response.raise_for_status()
    return True
