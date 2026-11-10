from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class VectorStore:

    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.chunks = []
        self.matrix = None

    def add_documents(self, documents):

        if not documents:
            return

        self.chunks.extend(documents)

        texts = [doc["text"] for doc in self.chunks]

        self.matrix = self.vectorizer.fit_transform(texts)

    def search(self, question, top_k=3):

        if self.matrix is None or not self.chunks:
            return []

        question_vector = self.vectorizer.transform([question])

        scores = cosine_similarity(
            question_vector,
            self.matrix
        )[0]

        top_indices = scores.argsort()[::-1][:top_k]

        results = []

        for index in top_indices:

            if scores[index] <= 0:
                continue

            result = self.chunks[index].copy()
            result["score"] = float(scores[index])

            results.append(result)

        return results