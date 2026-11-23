from app.rag.embeddings import cosine_similarity, embed_text
from app.rag.ingestion import chunk_text
from tests.conftest import auth_header, register


def test_embedding_is_stable_and_chunking_preserves_text():
    assert embed_text("매출 보고서") == embed_text("매출 보고서")
    assert cosine_similarity(embed_text("매출"), embed_text("매출")) > 0.99
    assert "".join(chunk_text("가나다라", size=2)) == "가나다라"


def test_uploaded_document_is_used_as_the_answer_context(client, fake_models):
    owner = register(client, "rag@example.com", "Rag Co")
    headers = auth_header(owner["access_token"])
    created = client.post(
        "/api/v1/knowledge/documents",
        headers=headers,
        json={"title": "매출 메모", "filename": "sales.md", "content": "3월 매출은 420입니다. 담당자는 김하늘입니다."},
    )
    assert created.status_code == 201, created.text
    answer = client.post(
        "/api/v1/knowledge/ask",
        headers=headers,
        json={"query": "3월 매출은 얼마인가", "provider": "openai", "model": "gpt-test"},
    )
    assert answer.status_code == 200, answer.text
    assert "420" in answer.json()["answer"]
    assert answer.json()["sources"]

    other = register(client, "other-rag@example.com", "Other Co")
    hidden = client.post(
        "/api/v1/knowledge/ask",
        headers=auth_header(other["access_token"]),
        json={"query": "3월 매출은 얼마인가", "provider": "openai", "model": "gpt-test"},
    )
    assert "420" not in hidden.json()["answer"]
