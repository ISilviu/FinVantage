# Create your views here.

from django.http import JsonResponse
from langchain import hub
from pgvector.django import CosineDistance

from embeds.models import CURRENT_MODEL, FinancialStatementAnalysis


def financial_query(request):
    if request.method == "GET":
        question = request.GET.get("question")
        if question:
            embeddings = CURRENT_MODEL.embedding_model(
                model=CURRENT_MODEL.model_name,
            )

            question_embedding = embeddings.embed_query(question)
            context_texts = FinancialStatementAnalysis.objects.order_by(
                CosineDistance("embedding", question_embedding)
            ).values_list("analysis_text", flat=True)[:2]

            context = "\n\n".join(context_texts)

            prompt = hub.pull("rlm/rag-prompt")
            llm = CURRENT_MODEL.chat_model(
                model=CURRENT_MODEL.chat_model_name, temperature=0
            )

            prompt = prompt.invoke({"question": question, "context": context})
            answer = llm.invoke(prompt)

            response = {"question": question, "answer": answer.content}
        else:
            response = {"error": "No question provided"}

        return JsonResponse(response)
