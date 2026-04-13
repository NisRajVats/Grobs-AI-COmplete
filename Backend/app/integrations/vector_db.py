"""
Vector Database Service

Unified interface for vector database operations.
Supports Pinecone, Weaviate, Chroma, and FAISS.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class VectorDBProvider(Enum):
    """Supported vector database providers."""
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    CHROMA = "chroma"
    FAISS = "faiss"
    NONE = "none"


@dataclass
class SearchResult:
    """Represents a vector search result."""
    id: str
    score: float
    metadata: Dict[str, Any]


@dataclass
class VectorEntry:
    """Represents a vector entry."""
    id: str
    vector: List[float]
    metadata: Dict[str, Any]


class VectorDBInterface(ABC):
    """Abstract interface for vector database operations."""
    
    @abstractmethod
    def create_collection(self, name: str, dimension: int) -> bool:
        pass
    
    @abstractmethod
    def delete_collection(self, name: str) -> bool:
        pass
    
    @abstractmethod
    def add_vectors(self, collection: str, vectors: List[VectorEntry]) -> bool:
        pass
    
    @abstractmethod
    def search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        pass
    
    @abstractmethod
    def delete_vector(self, collection: str, vector_id: str) -> bool:
        pass


class PineconeService(VectorDBInterface):
    """Pinecone vector database implementation."""
    
    def __init__(self):
        try:
            from pinecone import Pinecone
            self.client = Pinecone(api_key=settings.PINECONE_API_KEY)
            self.indexes = {}
            logger.info("Pinecone client initialized")
        except ImportError:
            logger.warning("Pinecone not installed")
            self.client = None
    
    def _get_index(self, name: str):
        if name not in self.indexes:
            self.indexes[name] = self.client.Index(name)
        return self.indexes[name]
    
    def create_collection(self, name: str, dimension: int) -> bool:
        try:
            if name not in self.client.list_indexes().names():
                self.client.create_index(name=name, dimension=dimension, metric="cosine")
            return True
        except Exception as e:
            logger.error(f"Failed to create Pinecone index: {e}")
            return False
    
    def delete_collection(self, name: str) -> bool:
        try:
            self.client.delete_index(name)
            return True
        except Exception as e:
            logger.error(f"Failed to delete Pinecone index: {e}")
            return False
    
    def add_vectors(self, collection: str, vectors: List[VectorEntry]) -> bool:
        try:
            index = self._get_index(collection)
            vectors_data = [
                {"id": v.id, "values": v.vector, "metadata": v.metadata}
                for v in vectors
            ]
            index.upsert(vectors=vectors_data)
            return True
        except Exception as e:
            logger.error(f"Failed to add vectors to Pinecone: {e}")
            return False
    
    def search(self, collection: str, query_vector: List[float], top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        try:
            index = self._get_index(collection)
            query_params = {"top_k": top_k}
            if filters:
                query_params["filter"] = filters
            results = index.query(vector=query_vector, **query_params)
            return [SearchResult(id=match.id, score=match.score, metadata=match.metadata) for match in results.matches]
        except Exception as e:
            logger.error(f"Pinecone search failed: {e}")
            return []
    
    def delete_vector(self, collection: str, vector_id: str) -> bool:
        try:
            index = self._get_index(collection)
            index.delete(ids=[vector_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete Pinecone vector: {e}")
            return False


class ChromaService(VectorDBInterface):
    """Chroma vector database implementation."""
    
    def __init__(self):
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=settings.chroma_persist_path)
            logger.info("Chroma client initialized")
        except ImportError:
            logger.warning("Chroma not installed")
            self.client = None
    
    def create_collection(self, name: str, dimension: int) -> bool:
        try:
            self.client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
            return True
        except Exception as e:
            logger.error(f"Failed to create Chroma collection: {e}")
            return False
    
    def delete_collection(self, name: str) -> bool:
        try:
            self.client.delete_collection(name)
            return True
        except Exception as e:
            logger.error(f"Failed to delete Chroma collection: {e}")
            return False
    
    def add_vectors(self, collection: str, vectors: List[VectorEntry]) -> bool:
        try:
            coll = self.client.get_or_create_collection(name=collection)
            coll.add(
                ids=[v.id for v in vectors],
                embeddings=[v.vector for v in vectors],
                metadatas=[v.metadata for v in vectors]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add vectors to Chroma: {e}")
            return False
    
    def search(self, collection: str, query_vector: List[float], top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        try:
            coll = self.client.get_or_create_collection(name=collection)
            results = coll.query(query_embeddings=[query_vector], n_results=top_k, where=filters)
            return [
                SearchResult(
                    id=results["ids"][0][i],
                    score=1 - results["distances"][0][i],
                    metadata=results["metadatas"][0][i]
                )
                for i in range(len(results["ids"][0]))
            ]
        except Exception as e:
            logger.error(f"Chroma search failed: {e}")
            return []
    
    def delete_vector(self, collection: str, vector_id: str) -> bool:
        try:
            coll = self.client.get_or_create_collection(name=collection)
            coll.delete(ids=[vector_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete Chroma vector: {e}")
            return False


class FAISSService(VectorDBInterface):
    """FAISS vector database implementation (in-memory)."""
    
    def __init__(self):
        try:
            import faiss
            self.faiss = faiss
            self.indexes: Dict[str, faiss.Index] = {}
            self.metadata: Dict[str, List[Dict]] = {}
            logger.info("FAISS initialized")
        except ImportError:
            logger.warning("FAISS not installed")
            self.faiss = None
    
    def create_collection(self, name: str, dimension: int) -> bool:
        try:
            index = self.faiss.IndexFlatIP(dimension)
            self.indexes[name] = index
            self.metadata[name] = []
            return True
        except Exception as e:
            logger.error(f"Failed to create FAISS index: {e}")
            return False
    
    def delete_collection(self, name: str) -> bool:
        try:
            if name in self.indexes:
                del self.indexes[name]
            if name in self.metadata:
                del self.metadata[name]
            return True
        except Exception as e:
            logger.error(f"Failed to delete FAISS index: {e}")
            return False
    
    def add_vectors(self, collection: str, vectors: List[VectorEntry]) -> bool:
        try:
            if collection not in self.indexes:
                dimension = len(vectors[0].vector) if vectors else 128
                self.create_collection(collection, dimension)
            
            index = self.indexes[collection]
            for v in vectors:
                vec = self.faiss.float_vector(v.vector)
                self.faiss.normalize_L2(vec)
                index.add(vec)
                self.metadata[collection].append({"id": v.id, "metadata": v.metadata})
            return True
        except Exception as e:
            logger.error(f"Failed to add vectors to FAISS: {e}")
            return False
    
    def search(self, collection: str, query_vector: List[float], top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        try:
            if collection not in self.indexes:
                return []
            index = self.indexes[collection]
            query = self.faiss.float_vector(query_vector)
            self.faiss.normalize_L2(query)
            distances, indices = index.search(query.reshape(1, -1), min(top_k, index.ntotal))
            results = []
            for i, idx in enumerate(indices[0]):
                if idx >= 0 and idx < len(self.metadata[collection]):
                    meta = self.metadata[collection][idx]
                    results.append(SearchResult(id=meta["id"], score=float(distances[0][i]), metadata=meta["metadata"]))
            return results
        except Exception as e:
            logger.error(f"FAISS search failed: {e}")
            return []
    
    def delete_vector(self, collection: str, vector_id: str) -> bool:
        logger.warning("FAISS does not support individual deletion without rebuild")
        return False


class VectorDBService:
    """Unified vector database service."""
    
    def __init__(self, provider: Optional[str] = None):
        self.provider_name = provider or settings.VECTOR_DB_PROVIDER
        self._initialize_provider()
    
    def _initialize_provider(self):
        if self.provider_name == "pinecone":
            self.provider = PineconeService()
        elif self.provider_name == "chroma":
            self.provider = ChromaService()
        elif self.provider_name == "faiss":
            self.provider = FAISSService()
        else:
            self.provider = None
            logger.warning(f"Unknown vector DB provider: {self.provider_name}")
    
    def create_collection(self, name: str, dimension: int = 384) -> bool:
        if not self.provider:
            logger.warning("No vector DB provider configured")
            return False
        return self.provider.create_collection(name, dimension)
    
    def delete_collection(self, name: str) -> bool:
        if not self.provider:
            return False
        return self.provider.delete_collection(name)
    
    def add_vectors(self, collection: str, vectors: List[VectorEntry]) -> bool:
        if not self.provider:
            return False
        return self.provider.add_vectors(collection, vectors)
    
    def search(self, collection: str, query_vector: List[float], top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        if not self.provider:
            return []
        return self.provider.search(collection, query_vector, top_k, filters)
    
    def delete_vector(self, collection: str, vector_id: str) -> bool:
        if not self.provider:
            return False
        return self.provider.delete_vector(collection, vector_id)
    
    def similarity_search(self, collection: str, text: str, top_k: int = 10, embed_func: Optional[callable] = None) -> List[SearchResult]:
        if not embed_func:
            from app.services.llm_service import llm_service
            embed_func = lambda t: llm_service.generate_embeddings(t)
        
        embeddings = embed_func([text])
        if not embeddings:
            return []
        return self.search(collection, embeddings[0].embedding, top_k)


# Singleton instance
vector_db_service = VectorDBService()
