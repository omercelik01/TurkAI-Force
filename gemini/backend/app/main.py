from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import numpy as np
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'lexidatabase')
COLLECTION_NAME = 'embeddings'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# MongoDB Connection
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Initialize Generative AI API
genai.configure(api_key=GEMINI_API_KEY)

# SentenceTransformer model
embedder = SentenceTransformer('all-mpnet-base-v2')

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class QueryRequest(BaseModel):
    query: str

# Cosine similarity function
def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# Find similar document
@app.post("/ask")
async def find_similar_document(request: QueryRequest):
    query = request.query
    # Convert user query to embedding
    query_embedding = embedder.encode([query], convert_to_numpy=True)

    # Fetch embeddings from MongoDB
    items = list(collection.find())

    if not items:
        raise HTTPException(status_code=404, detail="No embeddings found in the database.")

    best_similarity = -1
    best_match = None

    # Find the most similar document
    for item in items:
        if 'embedding' in item and isinstance(item['embedding'], list):
            embedding = np.array(item['embedding'], dtype=np.float32)
            similarity = cosine_similarity(query_embedding[0], embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = item

    if best_match:
        # Use the text field for more informative response
        response_text = best_match.get('text', "Metin mevcut değil.")

        # Generate answer using the context from the best match
        try:
            response = genai.generate_text(
                model="models/chat-bison-001",
                prompt=f"Kontekst: {response_text}\nSoru: {query}\nCevap:",
                max_output_tokens=200
            )
            answer = response.generations[0].text
        except Exception as e:
            answer = f"Cevap oluşturulurken bir hata oluştu: {str(e)}"

        return {
            "embedding_id": best_match.get('embedding_id', 'Unknown'),
            "similarity": round(float(best_similarity), 2),
            "text": response_text,
            "generated_answer": answer
        }
    else:
        raise HTTPException(status_code=404, detail="No similar document found.")

# Main entry point for local testing
@app.get("/ping")
async def ping():
    return {"message": "pong"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
