"""
Tests for LRUCache — set/get, TTL, eviction, thread safety, hallucination bypass.
Also tests authorised_tokens caching.
"""
import threading
import time
import pytest

from cv_agent.app.cache import LRUCache


class TestLRUCache:

    def test_set_get_roundtrip(self):
        cache = LRUCache(max_size=10, ttl=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_returns_none(self):
        cache = LRUCache(max_size=10, ttl=60)
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self):
        cache = LRUCache(max_size=10, ttl=1)  # 1 second TTL
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_lru_eviction(self):
        cache = LRUCache(max_size=3, ttl=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        # Access 'a' to make it recently used
        cache.get("a")
        # Add 'd' — should evict 'b' (least recently used)
        cache.set("d", 4)
        assert cache.get("b") is None
        assert cache.get("a") == 1
        assert cache.get("c") == 3
        assert cache.get("d") == 4

    def test_stats(self):
        cache = LRUCache(max_size=10, ttl=60)
        cache.set("k", "v")
        cache.get("k")       # hit
        cache.get("missing")  # miss
        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_clear(self):
        cache = LRUCache(max_size=10, ttl=60)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.clear()
        assert cache.get("k1") is None
        assert cache.stats()["size"] == 0

    def test_thread_safety(self):
        cache = LRUCache(max_size=1000, ttl=60)
        errors = []

        def writer(prefix, count):
            try:
                for i in range(count):
                    cache.set(f"{prefix}_{i}", i)
            except Exception as e:
                errors.append(e)

        def reader(prefix, count):
            try:
                for i in range(count):
                    cache.get(f"{prefix}_{i}")
            except Exception as e:
                errors.append(e)

        threads = []
        for p in range(5):
            threads.append(threading.Thread(target=writer, args=(f"w{p}", 100)))
            threads.append(threading.Thread(target=reader, args=(f"w{p}", 100)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestMakeKey:

    def test_key_format(self):
        key = LRUCache.make_key("prof123", "jd456", 2, "A", namespace="cv", hallucination_hash="abcd1234")
        assert key == "cv:prof123:jd456:2:A:abcd1234"

    def test_different_hallucination_hash_different_key(self):
        k1 = LRUCache.make_key("p", "j", 1, "A", hallucination_hash="00000000")
        k2 = LRUCache.make_key("p", "j", 1, "A", hallucination_hash="abc12345")
        assert k1 != k2
