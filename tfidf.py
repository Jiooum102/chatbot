import math
import re
import unicodedata
from collections import Counter, defaultdict
from typing import Iterable, List, Optional, Set


DEFAULT_STOPWORDS: Set[str] = {
    "la",
    "co",
    "khong",
    "va",
    "cho",
    "cua",
    "nhu",
    "nao",
    "bao",
    "nhieu",
    "trong",
    "voi",
    "shop",
    "oi",
    "day",
    "an",
    "duoc",
    "tai",
    "neu",
    "thi",
    "gia",
    "khach",
    "hang",
}


class TFIDFVectorizer:
    def __init__(self, stopwords: Optional[Set[str]] = None) -> None:
        self.vocabulary_: List[str] = []
        self.idf_: List[float] = []
        self.stopwords: Set[str] = stopwords or DEFAULT_STOPWORDS
        self._token_pattern = re.compile(r"\b[a-z0-9]+\b")

    def _normalize(self, text: str) -> str:
        normalized = unicodedata.normalize("NFD", text.lower())
        return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")

    def tokenize(self, text: str) -> List[str]:
        ascii_text = self._normalize(text)
        tokens = self._token_pattern.findall(ascii_text)
        return [token for token in tokens if token not in self.stopwords]

    def fit(self, documents: Iterable[str]) -> None:
        df_counter: defaultdict[str, int] = defaultdict(int)
        docs = list(documents)
        total_docs = len(docs)
        if total_docs == 0:
            self.vocabulary_ = []
            self.idf_ = []
            return

        for doc in docs:
            unique_tokens = set(self.tokenize(doc))
            for token in unique_tokens:
                df_counter[token] += 1

        self.vocabulary_ = sorted(df_counter.keys())
        self.idf_ = [
            math.log((1 + total_docs) / (1 + df_counter[token])) + 1.0
            for token in self.vocabulary_
        ]

    def transform(self, documents: Iterable[str]) -> List[List[float]]:
        if not self.vocabulary_:
            return [[0.0] for _ in documents]

        transformed: List[List[float]] = []
        for doc in documents:
            tokens = self.tokenize(doc)
            token_counts = Counter(tokens)
            doc_len = len(tokens) or 1
            vector = []
            for idx, term in enumerate(self.vocabulary_):
                tf = token_counts.get(term, 0) / doc_len
                vector.append(tf * self.idf_[idx])
            transformed.append(vector)
        return transformed

    def fit_transform(self, documents: Iterable[str]) -> List[List[float]]:
        docs = list(documents)
        self.fit(docs)
        return self.transform(docs)

    def transform_text(self, text: str) -> List[float]:
        transformed = self.transform([text])
        return transformed[0]
