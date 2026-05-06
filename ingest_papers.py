#!/usr/bin/env python3
"""
Paper Ingestion Pipeline for Critique-Oriented RAG
===================================================
Chunks markdown papers by section, attaches metadata (title, year, section),
and stores in ChromaDB with sentence-transformer embeddings for vector search.
Also builds a BM25 index for keyword search (hybrid retrieval).
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple

import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi
import numpy as np

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
PAPER_DIRS = [
    BASE_DIR / "research-methane-isotope-db" / "methane_isotope_db" / "mineru_extractions_trimmed",
    BASE_DIR / "research-methane-OH" / "research-methane-OH" / "papers_md_trimmed",
]
DB_DIR = BASE_DIR / "chroma_db"
BM25_INDEX_PATH = BASE_DIR / "bm25_index.json"
CHUNK_META_PATH = BASE_DIR / "chunk_metadata.json"

# Embedding model (runs locally, no API key needed)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Chunking parameters
MAX_CHUNK_CHARS = 2000  # ~500 tokens
MIN_CHUNK_CHARS = 100
OVERLAP_CHARS = 200


# ---------------------------------------------------------------------------
# Paper Metadata Extraction
# ---------------------------------------------------------------------------
def extract_metadata_from_filename(filename: str) -> Dict:
    """
    Extract paper title and year from filename like 'Chen2026PNAS.md'
    Convention: AuthorYYYYJournal.md or AuthorYYYYJournal_SI.md
    """
    stem = Path(filename).stem
    # Try to extract year (4 digits)
    year_match = re.search(r'(\d{4})', stem)
    year = int(year_match.group(1)) if year_match else 0
    
    # Author is everything before the year
    author = stem[:year_match.start()] if year_match else stem
    
    # Journal/type is after the year
    after_year = stem[year_match.end():] if year_match else ""
    
    # Check if it's supplementary info
    is_supplement = "_SI" in stem or "_SD" in stem or "supplement" in stem.lower()
    
    return {
        "title": stem,
        "author": author,
        "year": year,
        "journal": after_year.replace("_SI", "").replace("_SD", ""),
        "is_supplement": is_supplement,
        "filename": filename,
    }


# ---------------------------------------------------------------------------
# Section-Based Chunking
# ---------------------------------------------------------------------------
def detect_section(text: str) -> str:
    """Classify text into a section type based on headings and content."""
    text_lower = text.lower()
    
    # Check for section headers
    section_patterns = {
        "Abstract": [r"abstract", r"summary"],
        "Introduction": [r"introduction", r"^1\.\s"],
        "Methods": [r"method", r"experimental", r"model description", r"data and method",
                    r"materials and methods", r"approach"],
        "Results": [r"result", r"findings", r"observations"],
        "Discussion": [r"discussion", r"implications", r"interpretation"],
        "Conclusions": [r"conclusion", r"summary and conclusion", r"concluding remarks"],
        "References": [r"references", r"bibliography"],
        "Supplementary": [r"supplementary", r"supporting information", r"appendix"],
    }
    
    for section, patterns in section_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower[:200]):
                return section
    
    return "Body"


def chunk_paper(filepath: Path, metadata: Dict) -> List[Dict]:
    """
    Chunk a markdown paper by sections (headers) with metadata.
    Each chunk gets: text, title, year, section, chunk_id
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # Split by markdown headers (##, ###, ---Page---)
    # Also split by page markers common in MinerU output
    section_pattern = r'(?:^#{1,4}\s+.+$|^---\s*Page\s*\d+\s*---$)'
    parts = re.split(section_pattern, content, flags=re.MULTILINE)
    headers = re.findall(section_pattern, content, flags=re.MULTILINE)
    
    chunks = []
    current_section = "Abstract"  # Default for first section
    
    for i, part in enumerate(parts):
        text = part.strip()
        if len(text) < MIN_CHUNK_CHARS:
            continue
        
        # Update section based on header
        if i > 0 and i - 1 < len(headers):
            header_text = headers[i - 1]
            current_section = detect_section(header_text + "\n" + text[:200])
        elif i == 0:
            current_section = detect_section(text[:300])
        
        # Skip references section (not useful for parameter extraction)
        if current_section == "References":
            continue
        
        # Split long sections into sub-chunks
        if len(text) > MAX_CHUNK_CHARS:
            sub_chunks = split_long_text(text, MAX_CHUNK_CHARS, OVERLAP_CHARS)
        else:
            sub_chunks = [text]
        
        for j, chunk_text in enumerate(sub_chunks):
            chunk_id = hashlib.md5(
                f"{metadata['title']}_{i}_{j}_{chunk_text[:50]}".encode()
            ).hexdigest()[:16]
            
            chunks.append({
                "id": chunk_id,
                "text": chunk_text,
                "title": metadata["title"],
                "author": metadata["author"],
                "year": metadata["year"],
                "journal": metadata["journal"],
                "section": current_section,
                "is_supplement": metadata["is_supplement"],
                "filename": metadata["filename"],
            })
    
    return chunks


def split_long_text(text: str, max_chars: int, overlap: int) -> List[str]:
    """Split text into overlapping chunks at sentence boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            # Keep overlap from end of previous chunk
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_text + " " + sentence
        else:
            current_chunk += " " + sentence
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


# ---------------------------------------------------------------------------
# Build Vector Database (ChromaDB)
# ---------------------------------------------------------------------------
def build_vector_db(all_chunks: List[Dict]):
    """Store chunks in ChromaDB with sentence-transformer embeddings."""
    print(f"\nBuilding ChromaDB vector store at {DB_DIR}...")
    
    # Use sentence-transformers for embeddings
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    
    client = chromadb.PersistentClient(path=str(DB_DIR))
    
    # Delete existing collection if it exists
    try:
        client.delete_collection("papers")
    except:
        pass
    
    collection = client.create_collection(
        name="papers",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Batch insert (ChromaDB has limits on batch size)
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        
        ids = [c["id"] for c in batch]
        documents = [c["text"] for c in batch]
        metadatas = [{
            "title": c["title"],
            "author": c["author"],
            "year": c["year"],
            "journal": c["journal"],
            "section": c["section"],
            "is_supplement": c["is_supplement"],
            "filename": c["filename"],
        } for c in batch]
        
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        
        if (i + batch_size) % 500 == 0:
            print(f"  Inserted {min(i + batch_size, len(all_chunks))}/{len(all_chunks)} chunks...")
    
    print(f"  Total chunks in vector DB: {collection.count()}")
    return collection


# ---------------------------------------------------------------------------
# Build BM25 Index (Keyword Search)
# ---------------------------------------------------------------------------
def build_bm25_index(all_chunks: List[Dict]):
    """Build BM25 index for keyword search."""
    print("\nBuilding BM25 keyword index...")
    
    # Tokenize documents (simple whitespace + lowercasing)
    tokenized_docs = []
    for chunk in all_chunks:
        tokens = re.findall(r'\b\w+\b', chunk["text"].lower())
        tokenized_docs.append(tokens)
    
    bm25 = BM25Okapi(tokenized_docs)
    
    # Save metadata for retrieval
    chunk_meta = [{
        "id": c["id"],
        "title": c["title"],
        "year": c["year"],
        "section": c["section"],
        "text": c["text"][:200],  # Preview only for index file
    } for c in all_chunks]
    
    with open(CHUNK_META_PATH, 'w') as f:
        json.dump(chunk_meta, f)
    
    # Save BM25 corpus for reload
    with open(BM25_INDEX_PATH, 'w') as f:
        json.dump({
            "n_docs": len(tokenized_docs),
            "avg_doc_len": float(np.mean([len(d) for d in tokenized_docs])),
        }, f)
    
    print(f"  BM25 index: {len(tokenized_docs)} documents, "
          f"avg {np.mean([len(d) for d in tokenized_docs]):.0f} tokens/doc")
    
    return bm25, tokenized_docs


# ---------------------------------------------------------------------------
# Main Ingestion Pipeline
# ---------------------------------------------------------------------------
def main():
    print("="*70)
    print("PAPER INGESTION PIPELINE")
    print("Critique-Oriented RAG for Methane Isotope Box Model")
    print("="*70)
    
    # Collect all paper files
    all_files = []
    for paper_dir in PAPER_DIRS:
        if paper_dir.exists():
            md_files = sorted(paper_dir.glob("*.md"))
            all_files.extend(md_files)
            print(f"\n  Found {len(md_files)} papers in {paper_dir.name}")
        else:
            print(f"\n  WARNING: Directory not found: {paper_dir}")
    
    print(f"\n  Total papers to ingest: {len(all_files)}")
    
    # Chunk all papers
    all_chunks = []
    for filepath in all_files:
        metadata = extract_metadata_from_filename(filepath.name)
        chunks = chunk_paper(filepath, metadata)
        all_chunks.extend(chunks)
    
    print(f"\n  Total chunks generated: {len(all_chunks)}")
    
    # Statistics
    sections = {}
    years = {}
    for c in all_chunks:
        sections[c["section"]] = sections.get(c["section"], 0) + 1
        decade = (c["year"] // 10) * 10
        years[decade] = years.get(decade, 0) + 1
    
    print(f"\n  Chunks by section:")
    for sec, count in sorted(sections.items(), key=lambda x: -x[1]):
        print(f"    {sec}: {count}")
    
    print(f"\n  Chunks by decade:")
    for dec, count in sorted(years.items()):
        print(f"    {dec}s: {count}")
    
    # Build vector DB
    build_vector_db(all_chunks)
    
    # Build BM25 index
    build_bm25_index(all_chunks)
    
    # Save full chunk texts for BM25 retrieval
    full_chunks_path = BASE_DIR / "all_chunks.json"
    with open(full_chunks_path, 'w') as f:
        json.dump(all_chunks, f)
    print(f"\n  Full chunk data saved to: {full_chunks_path}")
    
    print(f"\n{'='*70}")
    print("INGESTION COMPLETE")
    print(f"{'='*70}")
    print(f"  Vector DB: {DB_DIR}")
    print(f"  BM25 metadata: {BM25_INDEX_PATH}")
    print(f"  Full chunks: {full_chunks_path}")


if __name__ == "__main__":
    main()
