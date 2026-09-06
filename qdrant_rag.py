from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

class KnowledgeRetriever:
    """In-memory Qdrant instance running locally without external containers."""
    def __init__(self, collection_name: str = "voice_kb"):
        self.client = QdrantClient(":memory:")
        self.collection_name = collection_name
        self.encoder = TextEmbedding("BAAI/bge-small-en-v1.5")
        self._init_collection()
        self._seed_default_knowledge()

    def _init_collection(self):
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

    def _seed_default_knowledge(self):
        # 300-500 token chunk sizing
        sample_docs = [
            "We provide an ultra-low latency voice assistant capable of real-time speech-to-speech interaction. "
            "Our system processes streaming speech-to-text with Sarvam AI, retrieves vector knowledge from Qdrant in under 150ms, "
            "and streams tokenized responses using high-throughput LLMs to maintain total sub-1.5 second latency.",
            "Our knowledge base supports immediate lead capture and CRM synchronization through background asynchronous worker tasks. "
            "The assistant keeps track of short-term memory over the last 2 to 3 conversation turns while enforcing strict prompt context boundaries below 1000 tokens."
        ]
        self.seed_documents(sample_docs)

    def seed_documents(self, documents: list[str]):
        embeddings = list(self.encoder.embed(documents))
        points = [
            PointStruct(id=idx, vector=emb.tolist(), payload={"text": doc})
            for idx, (doc, emb) in enumerate(zip(documents, embeddings))
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)

    def retrieve_context(self, query: str, top_k: int = 2) -> str:
        """Retrieves top_k context chunks with under 150ms latency limit."""
        query_vector = list(self.encoder.embed([query]))[0].tolist()
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k
        )
        return "\n".join([hit.payload["text"] for hit in results])