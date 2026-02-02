import os
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "hackathon_projects_merged.csv")
INDEX_PATH = os.path.join(BASE_DIR, "faiss_index")

class RagEngine:
    def __init__(self, gemini_api_key=None):
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API Key is missing. Please provide it in the sidebar or .env file.")
        
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=self.api_key)
        self.vector_store = self._load_or_create_index()

    def _load_or_create_index(self):
        """
        Loads the FAISS index if it exists, otherwise builds it from the CSV.
        """
        # Note: If we switched embeddings, we MUST rebuild the index if it exists but was built with OpenAI.
        # For safety/simplicity in this migration, let's assume we might need to rebuild if the folder exists 
        # but is incompatible. However, checking compatibility is hard. 
        # Best practice: if the user switches providers, they should probably delete the old index manually or we force rebuild.
        # I'll just keep the loading logic but maybe add a comment. 
        # Actually, let's force a rebuild if it fails to load or just rely on standard check.
        
        if os.path.exists(INDEX_PATH):
            try:
                print(f"Loading existing FAISS index from {INDEX_PATH}...")
                return FAISS.load_local(INDEX_PATH, self.embeddings, allow_dangerous_deserialization=True)
            except Exception as e:
                print(f"Failed to load index (possibly incompatible embeddings): {e}")
                print("Rebuilding index...")
        
        print(f"Building new FAISS index from {DATA_PATH}...")
        if not os.path.exists(DATA_PATH):
            raise FileNotFoundError(f"Data file not found at {DATA_PATH}")

        df = pd.read_csv(DATA_PATH)
        df.fillna("", inplace=True)

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

        import time

        # Batch processing to respect rate limits
        # Gemini Free Tier: 15 Requests Per Minute (1 req every 4s).
        # We use batch_size=100 (efficient) and sleep 5s to stay safe.
        batch_size = 100 
        vector_store = None
        total_docs = len(documents)
        
        print(f"Embedding {total_docs} documents with batch size {batch_size}...")
        
        for i in range(0, total_docs, batch_size):
            batch = documents[i : i + batch_size]
            try:
                if vector_store is None:
                    vector_store = FAISS.from_documents(batch, self.embeddings)
                else:
                    vector_store.add_documents(batch)
                
                print(f"Processed {min(i + batch_size, total_docs)}/{total_docs} documents...")
                time.sleep(5) # Sleep 5s to stay under 15 RPM
            except Exception as e:
                print(f"Error processing batch {i}: {e}")
                # Wait longer if hit rate limit
                time.sleep(30)
                # Retry once
                try:
                    if vector_store is None:
                        vector_store = FAISS.from_documents(batch, self.embeddings)
                    else:
                        vector_store.add_documents(batch)
                except Exception as retry_e:
                     print(f"Failed retry on batch {i}: {retry_e}")

        if vector_store:
            vector_store.save_local(INDEX_PATH)
        return vector_store

    def calculate_novelty_score(self, idea_text):
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

        max_similarity_score = max(0.0, min(1.0, max_similarity_score))
        novelty_score = (1.0 - max_similarity_score) * 10
        
        return round(novelty_score, 1), similar_projects
