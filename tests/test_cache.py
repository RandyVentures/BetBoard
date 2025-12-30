from betboard.storage.cache import CacheStore


def test_cache_set_get() -> None:
    cache: CacheStore[str] = CacheStore()
    cache.set("key", "value", ttl_minutes=10)
    assert cache.get("key") == "value"


def test_cache_expiry() -> None:
    cache: CacheStore[str] = CacheStore()
    cache.set("key", "value", ttl_minutes=-1)
    assert cache.get("key") is None
