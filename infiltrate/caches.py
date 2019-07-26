"""Contains file_cache and mem_cache beaker caches."""
from beaker.cache import CacheManager
# noinspection PyProtectedMember
from beaker.util import parse_cache_config_options

_file_cache_opts = {
    'cache.type': 'file',
    'cache.data_dir': 'infiltrate/data/Beaker/tmp/cache/data',
    'cache.lock_dir': 'infiltrate/data/Beaker/tmp/cache/lock'
}
file_cache = CacheManager(**parse_cache_config_options(_file_cache_opts))

_mem_cache_opts = {
    'cache.type': 'memory'
}
mem_cache = CacheManager(**parse_cache_config_options(_mem_cache_opts))


def invalidate():
    from beaker.cache import cache_managers
    for _cache in cache_managers.values():
        _cache.clear()
