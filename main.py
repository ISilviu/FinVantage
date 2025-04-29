import time

from dotenv import load_dotenv
from langchain import hub
from langchain.chat_models import init_chat_model
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_mistralai import MistralAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    llm = init_chat_model("mistral-small-latest", model_provider="mistralai")
    embeddings = MistralAIEmbeddings(model="mistral-embed")
    vector_store = InMemoryVectorStore(embeddings)

    loader = PyPDFLoader("mediflow.pdf")
    docs = loader.load()
    for doc in docs:
        print(doc.page_content)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_splits = text_splitter.split_documents(docs)

    _ = vector_store.add_documents(documents=all_splits)

    # Define prompt for question-answering
    prompt = hub.pull("rlm/rag-prompt")

    # Define state for application
    class State(TypedDict):
        question: str
        context: List[Document]
        answer: str

    # Define application steps
    def retrieve(state: State):
        retrieved_docs = vector_store.similarity_search(state["question"])
        return {"context": retrieved_docs}

    def generate(state: State):
        docs_content = "\n\n".join(doc.page_content for doc in state["context"])
        messages = prompt.invoke(
            {"question": state["question"], "context": docs_content}
        )
        response = llm.invoke(messages)
        return {"answer": response.content}

    # Compile application and test
    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    graph = graph_builder.compile()

    time.sleep(60 * 3)
    response = graph.invoke({"question": "WHat's the budget of Mediflow?"})
    print(response["answer"])

    # print("Model loaded successfully.")
