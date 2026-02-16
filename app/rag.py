import google.generativeai as genai
import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class RAGPipeline:
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path="data/chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(name="knowledge_base")
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')

        if self.collection.count() == 0:
            print("Initializing Knowledge Base...")
            self._ingest_data()

    def _ingest_data(self):
        try:
            if not os.path.exists("data/knowledge_base.txt"):
                return

            with open("data/knowledge_base.txt", "r") as f:
                text = f.read()

            chunks = [p for p in text.split('\n\n') if p.strip()]

            if not chunks:
                return

            ids = [str(i) for i in range(len(chunks))]

            embeddings = []
            for chunk in chunks:
                result = genai.embed_content(
                    model="models/gemini-embedding-001",
                    content=chunk,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])

            self.collection.add(
                documents=chunks,
                embeddings=embeddings,
                ids=ids
            )
            print(f"Ingested {len(chunks)} chunks into ChromaDB.")
        except Exception as e:
            print(f"Error ingesting data: {e}")

    def retrieve(self, query: str, top_k: int = 3):
        # Embed query
        result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=query,
            task_type="retrieval_query"
        )
        query_embedding = result['embedding']

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        return results['documents'][0] if results['documents'] else []

    def verify_groundedness(self, query: str, context: list, answer: str) -> bool:
        context_str = "\n".join(context)
        prompt = f"""
        You are a groundedness checker.
        Context: {context_str}
        Question: {query}
        Proposed Answer: {answer}
        Task: Is the Proposed Answer fully supported by the Context? 
        If yes, output ONLY 'YES'.
        If no, output ONLY 'NO'.
        """
        response = self.model.generate_content(prompt)
        return "YES" in response.text.strip().upper()

    def query(self, user_query: str):
        context_chunks = self.retrieve(user_query)
        if not context_chunks:
            return {"answer": "No relevant documents found.", "grounded": False}

        context_str = "\n".join(context_chunks)

        prompt = f"Context: {context_str}\n\nQuestion: {user_query}\n\nAnswer based strictly on the context provided:"
        response = self.model.generate_content(prompt)
        candidate_answer = response.text.strip()

        is_grounded = self.verify_groundedness(user_query, context_chunks, candidate_answer)

        if not is_grounded:
            return {
                "answer": "Insufficient information in company policy to answer this question accurately.",
                "context": context_chunks,
                "grounded": False,
                "original_candidate": candidate_answer
            }

        return {
            "answer": candidate_answer,
            "context": context_chunks,
            "grounded": True
        }

rag_system = RAGPipeline()
