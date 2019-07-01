from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

_file_cache_opts = {
    'cache.type': 'file',
    'cache.data_dir': 'data/Beaker/tmp/cache/data',
    'cache.lock_dir': 'data/Beaker/tmp/cache/lock'
}
file_cache = CacheManager(**parse_cache_config_options(_file_cache_opts))

_mem_cache_opts = {
    'cache.type': 'memory'
}
mem_cache = CacheManager(**parse_cache_config_options(_mem_cache_opts))
