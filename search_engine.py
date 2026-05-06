#!/usr/bin/env python3
"""
Hybrid Search Engine for Critique-Oriented RAG
===============================================
Combines ChromaDB vector search (semantic) with BM25 keyword search.
Supports section filtering, year weighting, and Reciprocal Rank Fusion (RRF).
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "chroma_db"
CHUNKS_PATH = BASE_DIR / "all_chunks.json"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class HybridSearchEngine:
    """Hybrid vector + keyword search over paper chunks."""
    
    def __init__(self):
        print("Loading search engine...")
        
        # Load ChromaDB
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        self.chroma_client = chromadb.PersistentClient(path=str(DB_DIR))
        self.collection = self.chroma_client.get_collection(
            name="papers",
            embedding_function=ef
        )
        
        # Load full chunks for BM25
        with open(CHUNKS_PATH, 'r') as f:
            self.all_chunks = json.load(f)
        
        # Build BM25 index
        self.tokenized_docs = [
            re.findall(r'\b\w+\b', c["text"].lower())
            for c in self.all_chunks
        ]
        self.bm25 = BM25Okapi(self.tokenized_docs)
        
        # Build id→index mapping
        self.id_to_idx = {c["id"]: i for i, c in enumerate(self.all_chunks)}
        
        print(f"  Loaded {len(self.all_chunks)} chunks")
        print(f"  Vector DB: {self.collection.count()} documents")
    
    def vector_search(
        self,
        query: str,
        n_results: int = 20,
        section_filter: Optional[List[str]] = None,
        min_year: Optional[int] = None,
    ) -> List[Dict]:
        """Semantic search via ChromaDB embeddings."""
        where_filter = None
        conditions = []
        
        if section_filter:
            conditions.append({"section": {"$in": section_filter}})
        if min_year:
            conditions.append({"year": {"$gte": min_year}})
        
        if len(conditions) == 1:
            where_filter = conditions[0]
        elif len(conditions) > 1:
            where_filter = {"$and": conditions}
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        hits = []
        for i in range(len(results["ids"][0])):
            hits.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1.0 - results["distances"][0][i],  # cosine similarity
                "source": "vector",
            })
        
        return hits
    
    def keyword_search(
        self,
        query: str,
        n_results: int = 20,
        section_filter: Optional[List[str]] = None,
        min_year: Optional[int] = None,
    ) -> List[Dict]:
        """BM25 keyword search."""
        tokens = re.findall(r'\b\w+\b', query.lower())
        scores = self.bm25.get_scores(tokens)
        
        # Apply filters
        if section_filter or min_year:
            for i, chunk in enumerate(self.all_chunks):
                if section_filter and chunk["section"] not in section_filter:
                    scores[i] = 0
                if min_year and chunk["year"] < min_year:
                    scores[i] = 0
        
        # Get top results
        top_indices = np.argsort(scores)[::-1][:n_results]
        
        hits = []
        for idx in top_indices:
            if scores[idx] > 0:
                hits.append({
                    "id": self.all_chunks[idx]["id"],
                    "text": self.all_chunks[idx]["text"],
                    "metadata": {
                        "title": self.all_chunks[idx]["title"],
                        "year": self.all_chunks[idx]["year"],
                        "section": self.all_chunks[idx]["section"],
                        "author": self.all_chunks[idx]["author"],
                    },
                    "score": float(scores[idx]),
                    "source": "bm25",
                })
        
        return hits
    
    def hybrid_search(
        self,
        query: str,
        n_results: int = 15,
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4,
        section_filter: Optional[List[str]] = None,
        min_year: Optional[int] = None,
        year_boost: bool = True,
    ) -> List[Dict]:
        """
        Hybrid search using Reciprocal Rank Fusion (RRF).
        
        Combines vector (semantic) and BM25 (keyword) results.
        Optionally boosts recent papers.
        """
        k = 60  # RRF constant
        
        # Get results from both engines
        vector_hits = self.vector_search(query, n_results=n_results * 2,
                                         section_filter=section_filter,
                                         min_year=min_year)
        bm25_hits = self.keyword_search(query, n_results=n_results * 2,
                                        section_filter=section_filter,
                                        min_year=min_year)
        
        # Compute RRF scores
        rrf_scores = {}
        hit_data = {}
        
        for rank, hit in enumerate(vector_hits):
            doc_id = hit["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + vector_weight / (k + rank + 1)
            hit_data[doc_id] = hit
        
        for rank, hit in enumerate(bm25_hits):
            doc_id = hit["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + bm25_weight / (k + rank + 1)
            if doc_id not in hit_data:
                hit_data[doc_id] = hit
        
        # Year boost: newer papers get a small score multiplier
        if year_boost:
            for doc_id in rrf_scores:
                year = hit_data[doc_id]["metadata"].get("year", 2000)
                # Papers from 2020+ get up to 20% boost
                year_factor = 1.0 + max(0, (year - 2010)) * 0.015
                rrf_scores[doc_id] *= year_factor
        
        # Sort by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        results = []
        seen_titles = set()
        for doc_id in sorted_ids[:n_results]:
            hit = hit_data[doc_id]
            title = hit["metadata"].get("title", "")
            
            results.append({
                "id": doc_id,
                "text": hit["text"],
                "metadata": hit["metadata"],
                "rrf_score": rrf_scores[doc_id],
                "source": hit.get("source", "hybrid"),
            })
        
        return results
    
    def discrepancy_search(
        self,
        parameter_name: str,
        current_value: str,
        n_results: int = 15,
    ) -> List[Dict]:
        """
        Specialized search for finding parameter discrepancies.
        Searches for the parameter name + related concepts in Results and Discussion sections.
        """
        # Build a targeted query
        query = f"{parameter_name} {current_value} measurement estimate value"
        
        # Search in the most informative sections
        results = self.hybrid_search(
            query=query,
            n_results=n_results,
            section_filter=["Results", "Discussion", "Methods", "Abstract", "Body"],
            year_boost=True,
        )
        
        return results


def main():
    """Test the search engine."""
    engine = HybridSearchEngine()
    
    # Test queries relevant to the box model
    test_queries = [
        ("OH KIE kinetic isotope effect CH4 13C", "Looking for KIE_OH values"),
        ("δD tropical wetlands methane source signature", "Looking for wetland δD"),
        ("methane lifetime tropospheric OH", "Looking for lifetime estimates"),
        ("interhemispheric exchange time transport", "Transport parameters"),
        ("Cl sink marine boundary layer methane", "Cl sink strength"),
    ]
    
    for query, description in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"Purpose: {description}")
        print(f"{'='*60}")
        
        results = engine.hybrid_search(query, n_results=5)
        for i, r in enumerate(results):
            print(f"\n  [{i+1}] {r['metadata']['title']} ({r['metadata'].get('year', '?')})")
            print(f"      Section: {r['metadata'].get('section', '?')}")
            print(f"      RRF Score: {r['rrf_score']:.4f}")
            print(f"      Preview: {r['text'][:150]}...")


if __name__ == "__main__":
    main()
