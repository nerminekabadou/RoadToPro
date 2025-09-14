"""
Build a FAISS RAG index from LoL-V2T dataset with timing and progress estimation.
- Uses GPU for Ollama3 embeddings
- Samples 25% of data for quick testing
"""

import os
import json
import random
import time
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

ANNOTATION_FOLDER = "annotations/"
JSON_FILES = ["training.json", "validation.json", "testing.json"]
INDEX_PATH = "lol_rag_index"
SAMPLE_RATIO = 0.25
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50

# -----------------------------
# Step 1: Load documents
# -----------------------------
print("📄 Loading sentences...")
start_time = time.time()
docs = []

for file_name in JSON_FILES:
    path = os.path.join(ANNOTATION_FOLDER, file_name)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        for value in data.values():
            sentences = value.get("sentences", [])
            for s in sentences:
                if isinstance(s, list):
                    docs.extend(Document(page_content=item) for item in s if isinstance(item, str))
                elif isinstance(s, str):
                    docs.append(Document(page_content=s))

if not docs:
    raise ValueError("No sentences found in JSON files.")

print(f"✅ Total sentences loaded: {len(docs)} (time: {time.time() - start_time:.1f}s)")

# -----------------------------
# Step 2: Sample for faster testing
# -----------------------------
if SAMPLE_RATIO < 1.0:
    n_keep = max(1, int(len(docs) * SAMPLE_RATIO))
    docs = random.sample(docs, n_keep)
    print(f"📊 Using {len(docs)} docs for indexing (sample)")

# -----------------------------
# Step 3: Split text into chunks
# -----------------------------
split_start = time.time()
splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
splits = splitter.split_documents(docs)
print(f"✂️ Total chunks: {len(splits)} (split time: {time.time() - split_start:.1f}s)")

# -----------------------------
# Step 4: Build embeddings
# -----------------------------
print("⚡ Creating embeddings with Ollama3 (GPU if available)...")
embed_start = time.time()
embeddings = OllamaEmbeddings(model="llama3")

# Optional: show estimated time per 100 chunks
total_chunks = len(splits)
batch_size = 100
for i in range(0, total_chunks, batch_size):
    batch = splits[i:i+batch_size]
    _ = embeddings.embed_documents([doc.page_content for doc in batch])
    elapsed = time.time() - embed_start
    completed = i + len(batch)
    est_total = elapsed / completed * total_chunks
    remaining = est_total - elapsed
    print(f"⏱ Embedded {completed}/{total_chunks} chunks | elapsed: {elapsed:.1f}s | est remaining: {remaining:.1f}s")

# -----------------------------
# Step 5: Build and save FAISS index
# -----------------------------
print("🔍 Building FAISS index...")
faiss_start = time.time()
vectorstore = FAISS.from_documents(splits, embeddings)
os.makedirs(INDEX_PATH, exist_ok=True)
vectorstore.save_local(INDEX_PATH)

total_time = time.time() - start_time
print(f"🎉 RAG index saved to '{INDEX_PATH}' in {total_time:.1f}s total.")
