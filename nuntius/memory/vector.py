import logging
from datetime import datetime
from pathlib import Path

from ..config import DATA_DIR

logger = logging.getLogger("nuntius.memory.vector")

VECTOR_DB_PATH = DATA_DIR / "chroma"


class VectorMemory:
    def __init__(self, persist_dir: str = ""):
        self.persist_dir = persist_dir or str(VECTOR_DB_PATH)
        self._collection = None
        self._client = None
        self._available = False
        self._init()

    def _init(self):
        try:
            import chromadb
            self._client = chromadb.PersistentClient(path=self.persist_dir)
            self._collection = self._client.get_or_create_collection(
                name="nuntius_memory",
                metadata={"hnsw:space": "cosine"},
            )
            self._available = True
            logger.info(f"Vector memory at {self.persist_dir}")
        except ImportError:
            logger.warning("chromadb not installed. Vector memory disabled.")
        except Exception as e:
            logger.warning(f"Vector memory init failed: {e}")

    @property
    def available(self) -> bool:
        return self._available

    def add_message(self, conv_id: str, role: str, content: str, created_at: str = ""):
        if not self._available or not content:
            return
        if role in ("system", "tool"):
            return
        try:
            text = content[:2000]
            doc_id = f"{conv_id}_{role}_{datetime.now().timestamp()}"
            metadata = {
                "conv_id": conv_id,
                "role": role,
                "created_at": created_at or datetime.now().isoformat(),
            }
            self._collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id],
            )
        except Exception as e:
            logger.debug(f"Vector add failed: {e}")

    def search(self, query: str, n_results: int = 5, conv_id: str = "") -> list[dict]:
        if not self._available:
            return self._fallback_search(query, n_results)
        try:
            where = {"conv_id": conv_id} if conv_id else None
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
            )
            items = []
            for i, doc in enumerate(results.get("documents", [[]])[0]):
                meta = results.get("metadatas", [[]])[0][i] if results.get("metadatas") else {}
                items.append({
                    "content": doc[:300],
                    "conv_id": meta.get("conv_id", ""),
                    "role": meta.get("role", ""),
                    "timestamp": meta.get("created_at", ""),
                    "score": results.get("distances", [[]])[0][i] if results.get("distances") else 0,
                })
            return items
        except Exception as e:
            logger.debug(f"Vector search failed: {e}")
            return self._fallback_search(query, n_results)

    def _fallback_search(self, query: str, n_results: int = 5) -> list[dict]:
        try:
            from ..memory.store import MemoryStore
            from ..config import DATA_DIR
            db_path = str(Path(DATA_DIR) / "nuntius.db")
            store = MemoryStore.__new__(MemoryStore)
            store.db_path = db_path
            convs = store.list_conversations()
            results = []
            query_lower = query.lower()
            for conv in convs[:20]:
                msgs = store.get_conversation(conv["id"])
                for msg in msgs:
                    c = (msg.get("content") or "")
                    if query_lower in c.lower():
                        results.append({
                            "content": c[:300],
                            "conv_id": conv["id"],
                            "role": msg.get("role", ""),
                            "timestamp": conv.get("updated_at", ""),
                            "score": 0,
                        })
                        if len(results) >= n_results:
                            break
                if len(results) >= n_results:
                    break
            return results
        except Exception:
            return []

    def get_conversation_summary(self, conv_id: str) -> str:
        if not self._available:
            return ""
        try:
            results = self._collection.get(
                where={"conv_id": conv_id},
            )
            docs = results.get("documents", []) or []
            return "\n".join(docs[-10:])[:2000]
        except Exception:
            return ""

    def count(self) -> int:
        if not self._available:
            return 0
        try:
            return self._collection.count()
        except Exception:
            return 0

    def delete_conversation(self, conv_id: str):
        if not self._available:
            return
        try:
            self._collection.delete(where={"conv_id": conv_id})
        except Exception as e:
            logger.debug(f"Vector delete failed: {e}")

    def close(self):
        if self._client:
            try:
                self._client = None
                self._collection = None
            except Exception:
                pass
