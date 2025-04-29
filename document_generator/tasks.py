from datetime import datetime
import os

from celery import shared_task
from django.conf import settings
from langchain_mistralai import ChatMistralAI


@shared_task
def generate_hourly_document():
    """
    Generate a document every hour.
    """
    print("Generating content:")

    chat_model = ChatMistralAI(model="mistral-small")
    response = chat_model.invoke(
        "Write a technical specification for a login system. Use markdown."
    )

    print("Generated content:")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    document_name = f"specification_{timestamp}.md"

    document_path = f"{settings.GENERATED_DOCUMENTS_DIR}/{document_name}"

    os.makedirs(settings.GENERATED_DOCUMENTS_DIR, exist_ok=True)
    with open(document_path, "w") as file:
        file.write(response.content)
