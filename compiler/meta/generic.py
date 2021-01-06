import typing

import attr


@attr.s(frozen=True, slots=True)
class Generic:
    class_factory: typing.Callable = attr.ib()
    _cache: typing.MutableMapping = attr.ib(factory=dict)

    def __getitem__(self, item):
        if not isinstance(item, tuple):
            item = (item,)

        if item not in self._cache:
            self._cache[item] = self.class_factory(*item)

        return self._cache[item]
