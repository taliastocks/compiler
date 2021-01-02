import abc
import threading
import weakref


class InstanceCache(type):
    """Metaclass which causes a class to cache its instances.
    """
    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls.__instance_cache = weakref.WeakKeyDictionary()
        cls.__instance_cache_lock = threading.RLock()

    def __call__(cls, *args, **kwargs):
        new_instance = super().__call__(*args, **kwargs)
        new_instance_ref = weakref.ref(new_instance)

        with cls.__instance_cache_lock:
            # Get an existing instance if there is one, otherwise the new instance.
            chosen_instance = cls.__instance_cache.get(new_instance, new_instance_ref)() or new_instance

            # If the new instance is chosen, cache it.
            if chosen_instance is new_instance:
                cls.__instance_cache[new_instance] = new_instance_ref

        return chosen_instance


class InstanceCacheABCMeta(InstanceCache, abc.ABCMeta):
    """Same as InstanceCache, but also derives from abc.ABCMeta.
    """
