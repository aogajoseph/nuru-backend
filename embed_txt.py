import os
from dotenv import load_dotenv  # ✅ Added dotenv import
from openai import OpenAI
from chromadb import PersistentClient
from tiktoken import encoding_for_model

# ✅ Load variables from .env file
load_dotenv()

# ✅ Initialize OpenAI client with loaded key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Set up ChromaDB
chroma_client = PersistentClient(path="chromadb/")
collection = chroma_client.get_or_create_collection("church_docs")

# Utility: Count tokens for billing/debug
def count_tokens(text, model="text-embedding-3-small"):
    enc = encoding_for_model(model)
    return len(enc.encode(text))

# Load .txt file
def load_text_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

# Chunk the text (roughly 500 tokens per chunk)
def chunk_text(text, chunk_size=500):
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i:i + chunk_size])

# Embed and store
def embed_and_store(doc_id, text):
    for i, chunk in enumerate(chunk_text(text)):
        print(f"Embedding chunk {i}...")
        response = client.embeddings.create(
            input=chunk,
            model="text-embedding-3-small"
        )
        vector = response.data[0].embedding
        collection.add(
            documents=[chunk],
            embeddings=[vector],
            ids=[f"{doc_id}-{i}"]
        )

# === Run this file ===
if __name__ == "__main__":
    file_path = "sermon_sample.txt"  # Replace with your file
    doc_text = load_text_file(file_path)

    embed_and_store("sermon1", doc_text)

    # Persist the vector store
    chroma_client.persist()
    print("✅ Done. Vectors stored successfully.")
