from memory.store import MemoryStore


def test_memory_store_persists_entries():
    store = MemoryStore(path="data/test_memory.sqlite3")
    store.add_memory("conversation", "hello there")
    memories = store.list_memories("conversation")
    assert any(entry["content"] == "hello there" for entry in memories)
    store.close()
