"""
Embedding Service — v4
=======================
Semantic embeddings for skill matching and resume analysis.

Features:
- Multi-provider embedding generation (OpenAI, HuggingFace, local)
- Caching and vector optimization
- Cosine similarity matching with threshold-based filtering
- Batch processing support
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

EMBEDDING_CACHE_DIR = os.path.join(settings.CHROMA_PERSIST_DIR, "embedding_cache")
os.makedirs(EMBEDDING_CACHE_DIR, exist_ok=True)

# Pre-compiled skill taxonomy for semantic matching
SKILL_TAXONOMY = {
    "frontend": {
        "core": ["React", "Vue", "Angular", "Svelte", "Next.js", "Nuxt"],
        "languages": ["JavaScript", "TypeScript", "HTML", "CSS"],
        "tools": ["Webpack", "Vite", "Babel", "ESLint", "Prettier"],
        "concepts": ["Responsive Design", "Accessibility", "WCAG", "SEO", "PWA"]
    },
    "backend": {
        "core": ["Node.js", "Django", "Flask", "FastAPI", "Spring", "Express"],
        "languages": ["Python", "Java", "Go", "Ruby", "PHP", "C#"],
        "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch"],
        "concepts": ["REST", "GraphQL", "gRPC", "Microservices", "API Design"]
    },
    "devops": {
        "cloud": ["AWS", "Azure", "GCP", "DigitalOcean"],
        "containers": ["Docker", "Kubernetes", "Helm"],
        "ci_cd": ["Jenkins", "GitHub Actions", "GitLab CI", "CircleCI"],
        "iac": ["Terraform", "Ansible", "CloudFormation", "Pulumi"]
    },
    "data_science": {
        "ml": ["TensorFlow", "PyTorch", "scikit-learn", "XGBoost"],
        "analysis": ["Pandas", "NumPy", "SciPy", "Matplotlib"],
        "databases": ["SQL", "Spark", "Hadoop", "Kafka"],
        "deployment": ["MLflow", "Docker", "Kubernetes", "FastAPI"]
    }
}

# Skill similarity matrix (pre-computed for common pairs)
SKILL_SIMILARITY_CACHE = {}


class EmbeddingService:
    """
    Unified embedding service for semantic matching.
    Supports multiple providers with fallback mechanisms.
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize embedding service.
        
        Args:
            provider: Embedding provider (openai, huggingface, local)
        """
        self.provider = provider or settings.EMBEDDING_PROVIDER or "huggingface"
        self.model_name = settings.EMBEDDING_MODEL or "sentence-transformers/all-MiniLM-L6-v2"
        self.cache = {}
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model based on provider."""
        try:
            if self.provider == "openai":
                self._init_openai()
            elif self.provider == "huggingface":
                self._init_huggingface()
            else:
                self._init_huggingface()  # Default fallback
        except Exception as e:
            logger.warning(f"Failed to initialize embedding model: {e}. Using dummy embeddings.")
            self.model = None
    
    def _init_openai(self):
        """Initialize OpenAI embeddings."""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = "text-embedding-ada-002"
            logger.info("OpenAI embeddings initialized")
        except Exception as e:
            logger.warning(f"OpenAI embeddings not available: {e}")
            self._init_huggingface()
    
    def _init_huggingface(self):
        """Initialize HuggingFace sentence-transformers."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"HuggingFace embeddings initialized with {self.model_name}")
        except Exception as e:
            logger.warning(f"HuggingFace embeddings not available: {e}")
            self.model = None
    
    def get_embedding(self, text: str, use_cache: bool = True) -> Optional[List[float]]:
        """
        Get embedding vector for text.
        
        Args:
            text: Input text to embed
            use_cache: Whether to use cached embeddings
            
        Returns:
            Embedding vector as list of floats, or None if failed
        """
        if not text or not text.strip():
            return None
        
        # Check cache
        cache_key = f"{self.model_name}:{text.strip()[:100]}"
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        # Try to load from disk cache
        disk_cache_path = os.path.join(EMBEDDING_CACHE_DIR, f"{hash(cache_key)}.npy")
        if use_cache and os.path.exists(disk_cache_path):
            try:
                embedding = np.load(disk_cache_path).tolist()
                self.cache[cache_key] = embedding
                return embedding
            except Exception:
                pass
        
        # Generate embedding
        try:
            if self.provider == "openai" and hasattr(self, 'client'):
                embedding = self._get_openai_embedding(text)
            elif self.model is not None:
                embedding = self._get_huggingface_embedding(text)
            else:
                # Fallback to simple hash-based embedding
                embedding = self._get_dummy_embedding(text)
            
            # Cache result
            if use_cache:
                self.cache[cache_key] = embedding
                try:
                    np.save(disk_cache_path, np.array(embedding))
                except Exception:
                    pass
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return self._get_dummy_embedding(text)
    
    def _get_openai_embedding(self, text: str) -> List[float]:
        """Get embedding from OpenAI API."""
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    def _get_huggingface_embedding(self, text: str) -> List[float]:
        """Get embedding from HuggingFace model."""
        embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return embedding.tolist()
    
    def _get_dummy_embedding(self, text: str) -> List[float]:
        """Generate a deterministic dummy embedding based on text hash."""
        # Simple hash-based embedding for when no model is available
        # This ensures consistent behavior in tests/fallback scenarios
        np.random.seed(hash(text) % (2**32))
        return np.random.randn(384).tolist()  # Match MiniLM-L6-v2 dimension
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        
        if emb1 is None or emb2 is None:
            return 0.0
        
        similarity = cosine_similarity([emb1], [emb2])[0][0]
        return float(max(0.0, min(1.0, (similarity + 1) / 2)))  # Normalize to 0-1
    
    def match_skills_semantic(
        self,
        resume_skills: List[str],
        jd_skills: List[str],
        threshold: float = 0.75
    ) -> Dict[str, Any]:
        """
        Match resume skills against job description skills using semantic similarity.
        
        Args:
            resume_skills: Skills from resume
            jd_skills: Skills from job description
            threshold: Minimum similarity threshold for match
            
        Returns:
            Dictionary with matched, missing skills and match rate
        """
        if not jd_skills:
            return {"matched": [], "missing": [], "match_rate": 100.0}
        
        # Get embeddings for all skills
        resume_embeddings = {}
        jd_embeddings = {}
        
        for skill in resume_skills:
            emb = self.get_embedding(skill)
            if emb is not None:
                resume_embeddings[skill.lower()] = emb
        
        for skill in jd_skills:
            emb = self.get_embedding(skill)
            if emb is not None:
                jd_embeddings[skill.lower()] = emb
        
        matched = []
        missing = []
        
        for jd_skill in jd_skills:
            jd_skill_lower = jd_skill.lower()
            if jd_skill_lower in jd_embeddings:
                jd_emb = jd_embeddings[jd_skill_lower]
                
                # Find best match in resume skills
                best_similarity = 0.0
                best_match = None
                
                for resume_skill in resume_skills:
                    resume_skill_lower = resume_skill.lower()
                    if resume_skill_lower in resume_embeddings:
                        resume_emb = resume_embeddings[resume_skill_lower]
                        similarity = cosine_similarity([jd_emb], [resume_emb])[0][0]
                        similarity = (similarity + 1) / 2  # Normalize to 0-1
                        
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = resume_skill
                
                if best_similarity >= threshold and best_match:
                    matched.append(jd_skill)
                else:
                    missing.append(jd_skill)
            else:
                missing.append(jd_skill)
        
        match_rate = (len(matched) / len(jd_skills)) * 100 if jd_skills else 100.0
        
        return {
            "matched": matched,
            "missing": missing,
            "match_rate": round(match_rate, 2),
            "threshold": threshold
        }
    
    def get_skill_category(self, skill: str) -> str:
        """
        Determine the category of a skill using semantic matching.
        
        Args:
            skill: Skill name
            
        Returns:
            Category string (e.g., "frontend", "backend", "devops")
        """
        skill_lower = skill.lower()
        
        # Check exact matches first
        for category, skills_dict in SKILL_TAXONOMY.items():
            for subcategory, skills_list in skills_dict.items():
                if skill_lower in [s.lower() for s in skills_list]:
                    return category
        
        # Use semantic similarity for fuzzy matching
        category_embeddings = {}
        for category in SKILL_TAXONOMY.keys():
            category_text = f"{category} development programming"
            emb = self.get_embedding(category_text)
            if emb is not None:
                category_embeddings[category] = emb
        
        if not category_embeddings:
            return "general"
        
        skill_emb = self.get_embedding(skill)
        if skill_emb is None:
            return "general"
        
        best_category = None
        best_similarity = 0.0
        
        for category, cat_emb in category_embeddings.items():
            similarity = cosine_similarity([skill_emb], [cat_emb])[0][0]
            similarity = (similarity + 1) / 2
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_category = category
        
        return best_category if best_similarity > 0.5 else "general"
    
    def batch_embed(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                if self.provider == "openai" and hasattr(self, 'client'):
                    # OpenAI batch processing
                    response = self.client.embeddings.create(
                        model=self.model,
                        input=batch
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                elif self.model is not None:
                    # HuggingFace batch processing
                    batch_embeddings = self.model.encode(
                        batch, 
                        convert_to_numpy=True, 
                        show_progress_bar=False,
                        batch_size=batch_size
                    ).tolist()
                else:
                    # Fallback
                    batch_embeddings = [self._get_dummy_embedding(t) for t in batch]
                
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
                # Fallback to individual embeddings
                for text in batch:
                    embeddings.append(self._get_dummy_embedding(text))
        
        return embeddings
    
    def clear_cache(self):
        """Clear in-memory cache."""
        self.cache.clear()
        logger.info("Embedding cache cleared")


# ─────────────────────────────────────────────────────────────────────────────
# Singleton instance
# ─────────────────────────────────────────────────────────────────────────────

_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the singleton embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service