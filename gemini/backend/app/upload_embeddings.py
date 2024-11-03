import os
import boto3
import io
import PyPDF2
import numpy as np
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'eu-north-1')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'lexidatabase')
S3_PREFIX = os.getenv('S3_PREFIX', 'pdfs/')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'lexidatabase')
COLLECTION_NAME = 'embeddings'

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)
 
# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Load SentenceTransformer model
embedder = SentenceTransformer('all-mpnet-base-v2')

# List PDF files from S3
def list_pdf_files_from_s3():
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=S3_PREFIX)
    pdf_files = []
    if 'Contents' in response:
        for obj in response['Contents']:
            if obj['Key'].endswith('.pdf'):
                pdf_files.append(obj['Key'])
    return pdf_files

# Extract text from PDF
def extract_text_from_s3_pdf(file_key):
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=file_key)
        pdf_content = response['Body'].read()
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        extracted_text = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text
        return extracted_text
    except Exception as e:
        print(f"PDF'den metin çıkarılırken bir hata oluştu: {str(e)}")
        return None

# Compute and save embeddings to MongoDB
def compute_and_save_embeddings():
    pdf_files = list_pdf_files_from_s3()
    for pdf_file in pdf_files:
        text = extract_text_from_s3_pdf(pdf_file)
        if text:
            text_chunks = [text[i:i + 500] for i in range(0, len(text), 500)]  # Split text into smaller chunks
            for chunk_index, chunk in enumerate(text_chunks):
                embedding = embedder.encode([chunk], convert_to_numpy=True)[0]
                # Save to MongoDB
                document = {
                    'embedding_id': f"{pdf_file}_{chunk_index}",
                    'embedding': embedding.tolist(),
                    'text': chunk
                }
                collection.insert_one(document)
                print(f"Embedding ve metin MongoDB'ye kaydedildi: {pdf_file}, Chunk: {chunk_index}")

if __name__ == "__main__":
    compute_and_save_embeddings()

