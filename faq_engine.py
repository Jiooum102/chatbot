from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import chromadb
from chromadb.config import Settings
from chromadb.errors import InvalidCollectionException, NotFoundError
from pathlib import Path

from knowledge_base import KB_FAQ
from tfidf import TFIDFVectorizer


@dataclass
class FAQResponse:
    answer: str
    matched_question: str
    similarity: float


class ElectroStoreFAQ:
    COLLECTION_NAME = "electrostore_faq"

    def __init__(self) -> None:
        self.vectorizer = TFIDFVectorizer()
        storage_path = Path(__file__).parent / "chroma_storage"
        storage_path.mkdir(exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(storage_path), settings=Settings(anonymized_telemetry=False))
        try:
            self.client.delete_collection(self.COLLECTION_NAME)
        except (InvalidCollectionException, NotFoundError, ValueError):
            pass

        self.collection = self.client.create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self._build_index()

    def _build_index(self) -> None:
        questions = [item["question"] for item in KB_FAQ]
        embeddings = self.vectorizer.fit_transform(questions)
        self.collection.add(
            ids=[item["id"] for item in KB_FAQ],
            documents=questions,
            metadatas=[{"answer": item["answer"]} for item in KB_FAQ],
            embeddings=embeddings,
        )

    def ask(self, question: str, min_similarity: float = 0.3) -> Optional[FAQResponse]:
        normalized = question.strip()
        if not normalized:
            return None

        query_vector = self.vectorizer.transform_text(normalized)
        if not any(value != 0.0 for value in query_vector):
            return None

        result = self.collection.query(query_embeddings=[query_vector], n_results=1)
        if not result["ids"] or not result["ids"][0]:
            return None

        distance = result.get("distances", [[1.0]])[0][0]
        similarity = 1.0 - distance
        if similarity < min_similarity:
            return None

        return FAQResponse(
            answer=result["metadatas"][0][0]["answer"],
            matched_question=result["documents"][0][0],
            similarity=similarity,
        )
