import os
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "hackathon_projects_merged.csv")
INDEX_PATH = os.path.join(BASE_DIR, "faiss_index")

class RagEngine:
    def __init__(self, gemini_api_key=None):
        # API key is no longer needed for embeddings, but we keep signature compatible
        self.api_key = gemini_api_key 
        
        # Use Local Embeddings (Free, Fast, No Rate Limits)
        # all-MiniLM-L6-v2 is a standard efficient model.
        print("Initializing Local Embeddings (HuggingFace)...")
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        except Exception as e:
            print(f"Error initializing HuggingFaceEmbeddings: {e}")
            raise e
            
        self.vector_store = self._load_or_create_index()

    def _load_or_create_index(self):
        """
        Loads the FAISS index if it exists, otherwise builds it from the CSV.
        """
        # If index exists, try to load it. 
        # CAUTION: If the index was built with a DIFFERENT model (Gemini), loading it with HF will fail or produce garbage.
        # We should probably force rebuild if we are switching models. 
        # But to be safe, let's try to load, and if it fails, rebuild.
        
        if os.path.exists(INDEX_PATH):
            try:
                print(f"Loading existing FAISS index from {INDEX_PATH}...")
                # allow_dangerous_deserialization is needed for local pickle files
                return FAISS.load_local(INDEX_PATH, self.embeddings, allow_dangerous_deserialization=True)
            except Exception as e:
                print(f"Failed to load index (likely incompatible webdings): {e}")
                print("Rebuilding index...")
        
        print(f"Building new FAISS index from {DATA_PATH}...")
        if not os.path.exists(DATA_PATH):
            raise FileNotFoundError(f"Data file not found at {DATA_PATH}")

        df = pd.read_csv(DATA_PATH)
        df = df.fillna("")

        documents = []
        for _, row in df.iterrows():
            page_content = f"Title: {row['title']}\nDescription: {row['description']}\nTech Stack: {row['tech_stack']}"
            metadata = {
                "title": row['title'],
                "description": row['description'],
                "tech_stack": row['tech_stack'],
                "is_winner": row.get('is_winner', False),
                "url": row.get('url', '')
            }
            documents.append(Document(page_content=page_content, metadata=metadata))

        # Local processing is fast, we can enable a larger batch size
        batch_size = 500 
        vector_store = None
        total_docs = len(documents)
        
        print(f"Embedding {total_docs} documents with batch size {batch_size} (Locally)...")
        
        for i in range(0, total_docs, batch_size):
            batch = documents[i : i + batch_size]
            try:
                if vector_store is None:
                    vector_store = FAISS.from_documents(batch, self.embeddings)
                else:
                    vector_store.add_documents(batch)
                
                print(f"Processed {min(i + batch_size, total_docs)}/{total_docs} documents...")
            except Exception as e:
                print(f"Error processing batch {i}: {e}")

        if vector_store:
            vector_store.save_local(INDEX_PATH)
        return vector_store

    def calculate_novelty_score(self, idea_text):
        if not self.vector_store:
             return 5.0, []

        results = self.vector_store.similarity_search_with_relevance_scores(idea_text, k=5)
        
        max_similarity_score = 0.0
        similar_projects = []

        if results:
            max_similarity_score = results[0][1] 
            
            for doc, score in results:
                similar_projects.append({
                    "title": doc.metadata.get("title", "Unknown"),
                    "description": doc.metadata.get("description", "No description"),
                    "similarity": score,
                    "url": doc.metadata.get("url", "")
                })

        # Relevance score in FAISS (cosine) is -1 to 1.
        # We clamp to 0-1
        max_similarity_score = max(0.0, min(1.0, max_similarity_score))
        
        # Novelty is inverse of similarity
        novelty_score = (1.0 - max_similarity_score) * 10
        
        return round(novelty_score, 1), similar_projects
