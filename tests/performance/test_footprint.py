import platform
import time
from typing import AsyncIterator

import aiomcache
import pytest
from glide import GlideClient, GlideClientConfiguration, NodeAddress


@pytest.fixture
async def valkey_client() -> AsyncIterator[GlideClient]:
    addresses = [NodeAddress("localhost", 6379)]
    conf = GlideClientConfiguration(addresses=addresses)
    client = await GlideClient.create(conf)

    yield client

    await client.close()


@pytest.mark.skipif(platform.python_implementation() == "PyPy", reason="Too slow")
class TestValkey:
    async def test_valkey_getsetdel(self, valkey_client, valkey_cache):
        N = 10000
        valkey_total_time = 0
        for _n in range(N):
            start = time.time()
            await valkey_client.set("hi", "value")
            await valkey_client.get("hi")
            await valkey_client.delete(["hi"])
            valkey_total_time += time.time() - start

        aiocache_total_time = 0
        for _n in range(N):
            start = time.time()
            await valkey_cache.set("hi", "value", timeout=0)
            await valkey_cache.get("hi", timeout=0)
            await valkey_cache.delete("hi", timeout=0)
            aiocache_total_time += time.time() - start

        print(
            "\n{:0.2f}/{:0.2f}: {:0.2f}".format(
                aiocache_total_time, valkey_total_time, aiocache_total_time / valkey_total_time
            )
        )
        print("aiocache avg call: {:0.5f}s".format(aiocache_total_time / N))
        print("valkey    avg call: {:0.5f}s".format(valkey_total_time / N))
        assert aiocache_total_time / valkey_total_time < 1.35

    async def test_valkey_multigetsetdel(self, valkey_client, valkey_cache):
        N = 5000
        valkey_total_time = 0
        values = ["a", "b", "c", "d", "e", "f"]
        for _n in range(N):
            start = time.time()
            await valkey_client.mset({x: x for x in values})
            await valkey_client.mget(values)
            for k in values:
                await valkey_client.delete([k])
            valkey_total_time += time.time() - start

        aiocache_total_time = 0
        for _n in range(N):
            start = time.time()
            await valkey_cache.multi_set([(x, x) for x in values], timeout=0)
            await valkey_cache.multi_get(values, timeout=0)
            for k in values:
                await valkey_cache.delete(k, timeout=0)
            aiocache_total_time += time.time() - start

        print(
            "\n{:0.2f}/{:0.2f}: {:0.2f}".format(
                aiocache_total_time, valkey_total_time, aiocache_total_time / valkey_total_time
            )
        )
        print("aiocache avg call: {:0.5f}s".format(aiocache_total_time / N))
        print("valkey_client    avg call: {:0.5f}s".format(valkey_total_time / N))
        assert aiocache_total_time / valkey_total_time < 1.35


@pytest.fixture
async def aiomcache_pool():
    client = aiomcache.Client("127.0.0.1", 11211, pool_size=1)
    yield client
    await client.close()


@pytest.mark.skipif(platform.python_implementation() == "PyPy", reason="Too slow")
class TestMemcached:
    async def test_memcached_getsetdel(self, aiomcache_pool, memcached_cache):
        N = 10000
        aiomcache_total_time = 0
        for _n in range(N):
            start = time.time()
            await aiomcache_pool.set(b"hi", b"value")
            await aiomcache_pool.get(b"hi")
            await aiomcache_pool.delete(b"hi")
            aiomcache_total_time += time.time() - start

        aiocache_total_time = 0
        for _n in range(N):
            start = time.time()
            await memcached_cache.set("hi", "value", timeout=0)
            await memcached_cache.get("hi", timeout=0)
            await memcached_cache.delete("hi", timeout=0)
            aiocache_total_time += time.time() - start

        print(
            "\n{:0.2f}/{:0.2f}: {:0.2f}".format(
                aiocache_total_time,
                aiomcache_total_time,
                aiocache_total_time / aiomcache_total_time,
            )
        )
        print("aiocache avg call: {:0.5f}s".format(aiocache_total_time / N))
        print("aiomcache avg call: {:0.5f}s".format(aiomcache_total_time / N))
        assert aiocache_total_time / aiomcache_total_time < 1.40

    async def test_memcached_multigetsetdel(self, aiomcache_pool, memcached_cache):
        N = 2000
        aiomcache_total_time = 0
        values = [b"a", b"b", b"c", b"d", b"e", b"f"]
        for _n in range(N):
            start = time.time()
            for k in values:
                await aiomcache_pool.set(k, k)
            await aiomcache_pool.multi_get(*values)
            for k in values:
                await aiomcache_pool.delete(k)
            aiomcache_total_time += time.time() - start

        aiocache_total_time = 0
        values = ["a", "b", "c", "d", "e", "f"]
        for _n in range(N):
            start = time.time()
            await memcached_cache.multi_set([(x, x) for x in values], timeout=0)
            await memcached_cache.multi_get(values, timeout=0)
            for k in values:
                await memcached_cache.delete(k, timeout=0)
            aiocache_total_time += time.time() - start

        print(
            "\n{:0.2f}/{:0.2f}: {:0.2f}".format(
                aiocache_total_time,
                aiomcache_total_time,
                aiocache_total_time / aiomcache_total_time,
            )
        )
        print("aiocache avg call: {:0.5f}s".format(aiocache_total_time / N))
        print("aiomcache avg call: {:0.5f}s".format(aiomcache_total_time / N))
        assert aiocache_total_time / aiomcache_total_time < 1.40
