"""
PRAAPTI AI - OpenSearch Scheme Indexer & Hybrid Retrieval Client
Handles OpenSearch index creation, vector/BM25 scheme ingestion, and profile-based filtering.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
logger = logging.getLogger("praapti.scheme_indexer")
logging.basicConfig(level=logging.INFO)

try:
    from opensearchpy import OpenSearch, RequestsHttpConnection, helpers
    HAS_OPENSEARCH_LIB = True
except ImportError:
    OpenSearch = None
    RequestsHttpConnection = None
    helpers = None
    HAS_OPENSEARCH_LIB = False
    logger.warning("opensearch-py is not installed. Operating in local in-memory dataset mode.")

INDEX_NAME = os.getenv("OPENSEARCH_INDEX_NAME", "praapti-schemes")
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", "9200"))
SCHEMES_FILE_PATH = os.path.join(os.path.dirname(__file__), "../data/schemes.json")

INDEX_SETTINGS = {
    "settings": {
        "index": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "knn": True
        }
    },
    "mappings": {
        "properties": {
            "scheme_id": {"type": "keyword"},
            "title": {"type": "text", "analyzer": "standard"},
            "short_code": {"type": "keyword"},
            "level": {"type": "keyword"},
            "ministry": {"type": "text"},
            "category": {"type": "keyword"},
            "description": {"type": "text"},
            "benefits": {"type": "text"},
            "eligibility": {
                "properties": {
                    "target_group": {"type": "text"},
                    "max_annual_income": {"type": "long"},
                    "gender": {"type": "keyword"},
                    "age_min": {"type": "integer"},
                    "age_max": {"type": "integer"}
                }
            },
            "documents_required": {"type": "text"},
            "official_portal": {"type": "keyword"},
            "is_active": {"type": "boolean"}
        }
    }
}

class SchemeIndexer:
    """Manages OpenSearch connection, index lifecycle, and citizen-matching search queries."""

    def __init__(self, host: str = OPENSEARCH_HOST, port: int = OPENSEARCH_PORT):
        self.host = host
        self.port = port
        self.client: Optional[OpenSearch] = None
        self._init_client()

    def _init_client(self):
        """Initializes connection to local OpenSearch cluster."""
        if not HAS_OPENSEARCH_LIB:
            self.client = None
            return

        try:
            self.client = OpenSearch(
                hosts=[{'host': self.host, 'port': self.port}],
                http_auth=None,
                use_ssl=False,
                verify_certs=False,
                connection_class=RequestsHttpConnection,
                timeout=5
            )
            # Test ping
            if self.client.ping():
                logger.info(f"Connected to OpenSearch cluster at {self.host}:{self.port}")
            else:
                logger.warning(f"OpenSearch at {self.host}:{self.port} unreachable. Will use local data fallback.")
                self.client = None
        except Exception as e:
            logger.warning(f"Could not connect to OpenSearch ({e}). Operating in local fallback mode.")
            self.client = None

    def create_index(self, force: bool = False) -> bool:
        """Creates the schemes index with mappings."""
        if not self.client:
            logger.info("OpenSearch client offline. Skipping remote index creation.")
            return False
        
        try:
            if self.client.indices.exists(index=INDEX_NAME):
                if force:
                    logger.info(f"Deleting existing index: {INDEX_NAME}")
                    self.client.indices.delete(index=INDEX_NAME)
                else:
                    logger.info(f"Index '{INDEX_NAME}' already exists.")
                    return True

            self.client.indices.create(index=INDEX_NAME, body=INDEX_SETTINGS)
            logger.info(f"Created index: {INDEX_NAME}")
            return True
        except Exception as e:
            logger.error(f"Error creating OpenSearch index: {e}")
            return False

    def ingest_schemes(self, file_path: str = SCHEMES_FILE_PATH) -> int:
        """Ingests scheme documents from schemes.json into OpenSearch."""
        if not os.path.exists(file_path):
            logger.error(f"Schemes file not found: {file_path}")
            return 0

        with open(file_path, "r", encoding="utf-8") as f:
            schemes_data = json.load(f)

        if not self.client:
            logger.info(f"OpenSearch offline. Loaded {len(schemes_data)} schemes locally.")
            return len(schemes_data)

        actions = [
            {
                "_index": INDEX_NAME,
                "_id": scheme.get("scheme_id", f"scheme_{idx}"),
                "_source": scheme
            }
            for idx, scheme in enumerate(schemes_data)
        ]

        try:
            success_count, errors = helpers.bulk(self.client, actions, refresh=True)
            logger.info(f"Successfully indexed {success_count} welfare schemes into OpenSearch.")
            return success_count
        except Exception as e:
            logger.error(f"Failed to bulk index schemes: {e}")
            return 0

    def search_schemes(
        self,
        query: str = "",
        category: Optional[str] = None,
        annual_income: Optional[int] = None,
        gender: Optional[str] = None,
        age: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search for schemes matching query and citizen eligibility parameters.
        Falls back to local file filtering if OpenSearch is not running.
        """
        if self.client:
            try:
                must_clauses: List[Dict[str, Any]] = []
                filter_clauses: List[Dict[str, Any]] = [{"term": {"is_active": True}}]

                if query:
                    must_clauses.append({
                        "multi_match": {
                            "query": query,
                            "fields": ["title^3", "description^2", "benefits", "eligibility.target_group^2"],
                            "fuzziness": "AUTO"
                        }
                    })
                else:
                    must_clauses.append({"match_all": {}})

                if category:
                    filter_clauses.append({"term": {"category": category}})

                if gender and gender.lower() != "all":
                    filter_clauses.append({
                        "bool": {
                            "should": [
                                {"term": {"eligibility.gender": "All"}},
                                {"term": {"eligibility.gender": gender}}
                            ]
                        }
                    })

                search_body = {
                    "size": limit,
                    "query": {
                        "bool": {
                            "must": must_clauses,
                            "filter": filter_clauses
                        }
                    }
                }

                response = self.client.search(index=INDEX_NAME, body=search_body)
                hits = response.get("hits", {}).get("hits", [])
                return [hit["_source"] for hit in hits]
            except Exception as e:
                logger.error(f"OpenSearch query failed: {e}. Falling back to local data.")

        # Local Fallback Search
        return self._local_search(query, category, annual_income, gender, age, limit)

    def _local_search(
        self,
        query: str,
        category: Optional[str],
        annual_income: Optional[int],
        gender: Optional[str],
        age: Optional[int],
        limit: int
    ) -> List[Dict[str, Any]]:
        """In-memory matching when OpenSearch container is inactive."""
        if not os.path.exists(SCHEMES_FILE_PATH):
            return []

        with open(SCHEMES_FILE_PATH, "r", encoding="utf-8") as f:
            schemes = json.load(f)

        results = []
        q_lower = query.lower() if query else ""

        for s in schemes:
            if not s.get("is_active", True):
                continue

            # Category match
            if category and s.get("category", "").lower() != category.lower():
                continue

            # Gender match
            el_gender = s.get("eligibility", {}).get("gender", "All")
            if gender and el_gender != "All" and el_gender.lower() != gender.lower():
                continue

            # Income filter
            max_income = s.get("eligibility", {}).get("max_annual_income")
            if annual_income and max_income and annual_income > max_income:
                continue

            # Age filter
            min_age = s.get("eligibility", {}).get("age_min", 0)
            max_age = s.get("eligibility", {}).get("age_max", 120)
            if age and (age < min_age or age > max_age):
                continue

            # Text relevance match
            if q_lower:
                text_corpus = f"{s.get('title','')} {s.get('description','')} {s.get('benefits','')} {s.get('category','')}".lower()
                if q_lower not in text_corpus:
                    continue

            results.append(s)
            if len(results) >= limit:
                break

        return results

# Shared indexer instance
scheme_indexer = SchemeIndexer()

if __name__ == "__main__":
    print("=== OpenSearch Scheme Indexer Initialization ===")
    scheme_indexer.create_index(force=True)
    count = scheme_indexer.ingest_schemes()
    print(f"Ingested {count} schemes.")
    
    print("\n--- Testing Search (Farmer / Agriculture) ---")
    res = scheme_indexer.search_schemes(query="farmer", category="Agriculture")
    for r in res:
        print(f"Matched Scheme: {r.get('title')} ({r.get('scheme_id')}) - Benefit: {r.get('benefits')[:60]}...")
