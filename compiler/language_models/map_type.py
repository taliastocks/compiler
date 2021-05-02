import attr


@attr.s(frozen=True, slots=True)
class MapItem:
    key = attr.ib()
    value = attr.ib()
