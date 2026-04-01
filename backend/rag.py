import hashlib
import logging
import os
from typing import Any, Dict, List

import numpy as np

try:
    import PyPDF2
except Exception:  # pragma: no cover - optional dependency
    PyPDF2 = None

try:
    import docx
except Exception:  # pragma: no cover - optional dependency
    docx = None

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover - optional dependency
    BeautifulSoup = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None

logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self):
        self.model = None
        self.documents = []
        self.embeddings = []
        self.embedding_backend = "hash-fallback"
        self.allow_model_download = os.getenv("RAG_ALLOW_MODEL_DOWNLOAD", "").lower() in {"1", "true", "yes"}

        if SentenceTransformer:
            try:
                self.model = SentenceTransformer(
                    'all-MiniLM-L6-v2',
                    local_files_only=not self.allow_model_download,
                )
                self.embedding_backend = "sentence-transformers"
            except Exception as e:
                logger.warning(f"Falling back to hash embeddings because transformer model could not load: {e}")
                self.model = None

    def _encode_text(self, text: str) -> np.ndarray:
        if self.model:
            return np.array(self.model.encode(text))

        vector = np.zeros(128, dtype=float)
        for token in text.lower().split():
            digest = hashlib.md5(token.encode("utf-8")).digest()
            vector[digest[0] % 128] += 1.0
        norm = np.linalg.norm(vector)
        return vector if norm == 0 else vector / norm

    def _chunk_text(self, text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
        if not text.strip():
            return []

        chunks = []
        start = 0
        while start < len(text):
            end = min(len(text), start + chunk_size)
            chunks.append(text[start:end].strip())
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
        return [chunk for chunk in chunks if chunk]
        
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            if not PyPDF2:
                logger.warning("PyPDF2 is not installed")
                return ""
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            if not docx:
                logger.warning("python-docx is not installed")
                return ""
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            return ""
    
    def extract_text_from_html(self, file_path: str) -> str:
        """Extract text from HTML file"""
        try:
            if not BeautifulSoup:
                logger.warning("BeautifulSoup is not installed")
                return ""
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                text = soup.get_text()
                return text
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {e}")
            return ""

    def extract_text_from_plain_text(self, file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error extracting text from plain text file: {e}")
            return ""
    
    def add_document(self, file_path: str, metadata: Dict[str, Any] = None):
        """Add a document to the RAG system"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            text = self.extract_text_from_docx(file_path)
        elif file_extension in ['.html', '.htm']:
            text = self.extract_text_from_html(file_path)
        elif file_extension in ['.txt', '.md', '.csv', '.json']:
            text = self.extract_text_from_plain_text(file_path)
        else:
            logger.warning(f"Unsupported file format: {file_extension}")
            return
        
        if text:
            chunks = self._chunk_text(text)
            # Create document entry
            document = {
                'path': file_path,
                'text': text,
                'chunks': chunks,
                'metadata': metadata or {}
            }

            # Add to collections
            self.documents.append(document)
            for index, chunk in enumerate(chunks or [text]):
                self.embeddings.append(
                    {
                        "embedding": self._encode_text(chunk),
                        "document_index": len(self.documents) - 1,
                        "chunk_index": index,
                        "text": chunk,
                        "citation": self._build_citation(file_path, index, chunk),
                    }
                )
            
            logger.info(f"Added document: {file_path}")
    
    def search_similar(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar documents based on query"""
        if not self.embeddings:
            return []
        
        # Generate query embedding
        query_embedding = self._encode_text(query)
        
        # Calculate similarities
        similarities = []
        for i, embedding_record in enumerate(self.embeddings):
            embedding = embedding_record["embedding"]
            similarity = np.dot(query_embedding, embedding) / (
                (np.linalg.norm(query_embedding) or 1.0) * (np.linalg.norm(embedding) or 1.0)
            )
            similarities.append((i, similarity))
        
        # Sort by similarity and get top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_results = similarities[:top_k]
        
        # Return document information
        results = []
        for idx, similarity in top_results:
            if similarity > 0.1:  # Only include if similarity is above threshold
                match = self.embeddings[idx]
                results.append({
                    'document': self.documents[match["document_index"]],
                    'chunk': match["text"],
                    'chunk_index': match["chunk_index"],
                    'similarity': similarity
                })
        
        return results

    def _build_citation(self, file_path: str, chunk_index: int, chunk_text: str) -> Dict[str, Any]:
        lines = [line for line in chunk_text.splitlines() if line.strip()]
        line_start = chunk_index * 40 + 1
        line_end = line_start + max(1, len(lines)) - 1
        page = chunk_index + 1
        return {
            "source": os.path.basename(file_path),
            "page": page,
            "line_start": line_start,
            "line_end": line_end,
            "chunk_index": chunk_index,
        }

    def summarize_document(self, filename: str, max_sections: int = 8) -> Dict[str, Any]:
        for doc in self.documents:
            if os.path.basename(doc["path"]) != filename:
                continue
            chunks = doc.get("chunks") or [doc["text"]]
            sections = []
            for index, chunk in enumerate(chunks[:max_sections]):
                preview = " ".join(chunk.split())[:320]
                sections.append(
                    {
                        "heading": f"Section {index + 1}",
                        "summary": preview,
                        "citation": self._build_citation(doc["path"], index, chunk),
                    }
                )
            return {
                "filename": filename,
                "sections": sections,
                "overall_summary": " ".join(section["summary"] for section in sections)[:1200],
            }
        return {"filename": filename, "sections": [], "overall_summary": ""}

    def get_sources(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        results = self.search_similar(query, top_k=top_k)
        sources = []
        for result in results:
            citation = self._build_citation(result["document"]["path"], result["chunk_index"], result["chunk"])
            sources.append(
                {
                    "type": "document",
                    "source": citation["source"],
                    "snippet": result["chunk"][:260],
                    "page": citation["page"],
                    "line_start": citation["line_start"],
                    "line_end": citation["line_end"],
                    "similarity": round(float(result["similarity"]), 3),
                }
            )
        return sources
    
    def get_context(self, query: str, max_tokens: int = 1000) -> str:
        """Get context from similar documents for a query"""
        search_results = self.search_similar(query)
        
        if not search_results:
            return ""
        
        # Build context from top results
        context_parts = []
        total_tokens = 0
        
        for result in search_results:
            doc_text = result['chunk']
            # Estimate tokens (roughly 4 characters per token)
            doc_tokens = len(doc_text) // 4
            
            if total_tokens + doc_tokens <= max_tokens:
                source_name = os.path.basename(result['document']['path'])
                context_parts.append(f"[Source: {source_name}]\n{doc_text}")
                total_tokens += doc_tokens
            else:
                # Truncate to fit within token limit
                remaining_tokens = max_tokens - total_tokens
                truncated_text = doc_text[:remaining_tokens * 4]
                source_name = os.path.basename(result['document']['path'])
                context_parts.append(f"[Source: {source_name}]\n{truncated_text}")
                break
        
        return "\n\n".join(context_parts)

# Global RAG instance
rag_system = RAGSystem()
