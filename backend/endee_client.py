import os
import httpx
from typing import List, Dict, Any

ENDEE_SERVER_URL = os.environ.get("ENDEE_SERVER_URL", "http://endee:8080/api/v1")
NDD_AUTH_TOKEN = os.environ.get("NDD_AUTH_TOKEN", "documind_secret_token")
COLLECTION_NAME = "documind"

class EndeeClient:
    def __init__(self):
        self.base_url = ENDEE_SERVER_URL
        self.headers = {"Authorization": f"Bearer {NDD_AUTH_TOKEN}"}
        
    def _create_client(self):
        return httpx.Client(base_url=self.base_url, headers=self.headers, timeout=30.0)

    def create_collection(self):
        try:
            with self._create_client() as client:
                resp = client.post("/collections", json={"name": COLLECTION_NAME, "dimension": 384})
        except Exception:
            pass

    def upsert_vectors(self, vectors: List[Dict[str, Any]]):
        with self._create_client() as client:
            resp = client.post(f"/collections/{COLLECTION_NAME}/vectors", json={"vectors": vectors})
            resp.raise_for_status()

    def similarity_search(self, query_vector: List[float], top_k: int = 5) -> List[Dict]:
        try:
            with self._create_client() as client:
                resp = client.post(
                    f"/collections/{COLLECTION_NAME}/search",
                    json={"vector": query_vector, "top_k": top_k}
                )
                if resp.status_code == 200:
                    return resp.json().get("results", [])
        except Exception:
            pass
        return []

    def delete_by_filter(self, doc_id: str):
        try:
            with self._create_client() as client:
                client.delete(f"/collections/{COLLECTION_NAME}/vectors", params={"filter_key": "doc_id", "filter_value": doc_id})
        except Exception:
            pass

    def get_stats(self) -> Dict:
        try:
            with self._create_client() as client:
                resp = client.get(f"/collections/{COLLECTION_NAME}/stats")
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass
        return {"status": "offline or empty"}

endee_client = EndeeClient()
