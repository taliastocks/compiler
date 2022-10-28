import typing

import attr
import immutabledict


@attr.s(frozen=True, slots=True)
class Generic:
    class_factory: typing.Callable = attr.ib()
    _cache: typing.MutableMapping = attr.ib(factory=dict)

    def __getitem__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], tuple):
            args = args[0]
        kwargs = immutabledict.immutabledict(kwargs)
        item = (args, kwargs)

        try:
            if item not in self._cache:
                self._cache[item] = self.class_factory(*args, **kwargs)
        except TypeError as exc:
            raise TypeError(f'problem with {item!r}') from exc

        return self._cache[item]
