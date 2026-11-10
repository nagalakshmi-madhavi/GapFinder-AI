
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# Load the embedding model
embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


# Create FAISS vector store
class VectorStore:

    def __init__(self):
        self.index = None
        self.chunks = []

    # Convert text chunks into embeddings
    def add_documents(self, documents):

        if not documents:
            return

        texts = [doc["text"] for doc in documents]

        embeddings = embedding_model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        embeddings = np.asarray(
            embeddings,
            dtype="float32"
        )

        # Create FAISS index
        if self.index is None:
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)

        self.index.add(embeddings)

        self.chunks.extend(documents)

    # Search for relevant document chunks
    def search(self, question, top_k=3):

        if self.index is None or not self.chunks:
            return []

        question_embedding = embedding_model.encode(
            [question],
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        question_embedding = np.asarray(
            question_embedding,
            dtype="float32"
        )

        scores, indices = self.index.search(
            question_embedding,
            min(top_k, len(self.chunks))
        )

        results = []

        for score, index in zip(scores[0], indices[0]):

            if index == -1:
                continue

            result = self.chunks[index].copy()
            result["score"] = float(score)

            results.append(result)

        return results
