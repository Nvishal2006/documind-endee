from typing import List, Dict, Tuple
from rank_bm25 import BM25Okapi
from database import get_bm25_data, get_chunk_by_id
from endee_client import endee_client
from ingestion import tokenize_for_bm25, encoder

def get_bm25_results(query: str, top_k: int = 60) -> List[Tuple[str, float]]:
    data = get_bm25_data()
    if not data:
        return []
    corpus_tokens = [d["tokens"] for d in data]
    chunk_ids = [d["chunk_id"] for d in data]
    
    bm25 = BM25Okapi(corpus_tokens)
    query_tokens = tokenize_for_bm25(query)
    scores = bm25.get_scores(query_tokens)
    
    results = [(chunk_ids[i], scores[i]) for i in range(len(chunk_ids))]
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]

def get_endee_results(query: str, top_k: int = 60) -> List[Tuple[str, float]]:
    query_vector = encoder.encode(query).tolist()
    results = endee_client.similarity_search(query_vector, top_k=top_k)
    return [(r["id"], r.get("score", 0.0)) for r in results]

def reciprocal_rank_fusion(list1: List[str], list2: List[str], k: int = 60) -> List[str]:
    scores = {}
    for rank, item in enumerate(list1):
        scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank + 1)
    for rank, item in enumerate(list2):
        scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank + 1)
    
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [item[0] for item in sorted_items]

def hybrid_search(query: str, final_top_k: int = 5) -> List[Dict]:
    bm25_results = get_bm25_results(query, top_k=60)
    endee_results = get_endee_results(query, top_k=60)
    
    bm25_ranked_ids = [r[0] for r in bm25_results]
    endee_ranked_ids = [r[0] for r in endee_results]
    
    fused_ids = reciprocal_rank_fusion(bm25_ranked_ids, endee_ranked_ids, k=60)
    
    final_chunks = []
    for chunk_id in fused_ids[:final_top_k]:
        chunk_data = get_chunk_by_id(chunk_id)
        if chunk_data:
            final_chunks.append(chunk_data)
            
    return final_chunks
