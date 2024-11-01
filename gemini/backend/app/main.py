from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import boto3
import numpy as np
import faiss
from dotenv import load_dotenv
import os
from sentence_transformers import SentenceTransformer
import io

# .env dosyasını yükle
load_dotenv()
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'eu-north-1')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'lexidatabase')

# S3 istemcisi oluştur
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# SentenceTransformer modeli
embedder = SentenceTransformer('all-mpnet-base-v2')

app = FastAPI()

# S3'ten embedding ve metinleri yükleme
def load_embeddings_and_texts():
    try:
        s3.download_file(BUCKET_NAME, "embeddings/embeddings.npy", "downloaded_embeddings.npy")
        embeddings = np.load("downloaded_embeddings.npy")
        s3.download_file(BUCKET_NAME, "embeddings/texts.txt", "downloaded_texts.txt")
        with open("downloaded_texts.txt", "r", encoding="utf-8") as f:
            texts = f.readlines()
        texts = [text.strip() for text in texts]
        return embeddings, texts
    except Exception as e:
        print(f"Error loading from S3: {e}")
        return None, None

# Kullanıcı sorgusu ile FAISS kullanarak en yakın sonucu bulma
def search_in_documents(embedding_array, query, texts):
    query_embedding = embedder.encode([query], convert_to_numpy=True)

    # FAISS index oluşturma
    dimension = embedding_array.shape[1]
    faiss_index = faiss.IndexFlatL2(dimension)

    # Embeddingleri ekleme
    faiss.normalize_L2(embedding_array)
    faiss_index.add(embedding_array)

    # Arama yapma
    faiss.normalize_L2(query_embedding)
    D, I = faiss_index.search(query_embedding, k=1)

    # En iyi sonucu döndürme
    index = I[0][0]
    if index < len(texts):
        return texts[index]
    else:
        return "Sorry, no answer found."

@app.get("/ask")
async def ask_question(query: str):
    embeddings, texts = load_embeddings_and_texts()
    if embeddings is None or texts is None:
        return JSONResponse(content={"error": "Unable to load embeddings or texts"}, status_code=500)
    
    response = search_in_documents(embeddings, query, texts)
    return JSONResponse(content={"answer": response})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
