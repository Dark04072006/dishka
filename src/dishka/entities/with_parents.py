from abc import ABC, ABCMeta
from enum import Enum
from types import GenericAlias
from typing import (
    TYPE_CHECKING,
    Final,
    Generic,
    TypeVar,
    _BaseGenericAlias,
    get_args,
)
from typing import (
    get_origin as typing_get_origin,
)

from dishka._adaptix.type_tools import is_generic
from dishka.entities.provides_marker import ProvideMultiple

IGNORE_TYPES: Final = (
    type,
    object,
    Enum,
    ABC,
    ABCMeta,
    Generic,
    Exception,
)


def get_origin(obj):
    return typing_get_origin(obj) or obj


def is_ignore_type(origin_obj):
    return get_origin(origin_obj) in IGNORE_TYPES


def get_parameters(obj):
    if hasattr(obj, "__parameters__"):
        return obj.__parameters__
    return ()


def parse_parameters_names(obj):
    return [param.__name__ for param in get_parameters(obj)]


def get_not_null_args(obj):
    return [
        arg
        for arg in get_args(obj)
        if not isinstance(arg, TypeVar)
    ]


def get_type_vars_map(obj):
    origin_obj = get_origin(obj)
    if not get_parameters(origin_obj):
        return {}

    return dict(
        zip(
            parse_parameters_names(origin_obj),
            get_not_null_args(obj), strict=False,
        ),
    )


def create_generic(origin_obj, type_vars_map):
    if is_generic(origin_obj):
        return origin_obj[
            *[
                type_vars_map[type_var]
                for type_var in parse_parameters_names(origin_obj)
            ]
        ]
    return None


def recursion_get_parents_for_generic_class(obj, parents, type_vars_map):
    origin_obj = get_origin(obj)
    if is_ignore_type(origin_obj):
        return

    type_vars_map.update(get_type_vars_map(obj))
    for obj in origin_obj.__orig_bases__:
        origin_obj = get_origin(obj)
        if is_ignore_type(origin_obj):
            continue

        type_vars_map.update(get_type_vars_map(obj))
        parents.append(create_generic(origin_obj, type_vars_map) or obj)
        recursion_get_parents_for_generic_class(obj, parents, type_vars_map)


def get_parents(obj):
    if is_ignore_type(get_origin(obj)):
        raise ValueError("The starting class %r is in ignored types" % obj)

    if isinstance(obj, (_BaseGenericAlias, GenericAlias)):
        res = []
        type_vars_map = get_type_vars_map(obj)
        res.append(create_generic(get_origin(obj), type_vars_map) or obj)
        recursion_get_parents_for_generic_class(obj, res, type_vars_map)
    elif hasattr(obj, "__orig_bases__"):
        res = []
        res.append(obj)
        recursion_get_parents_for_generic_class(obj, res, {})
    else:
        res = [obj_ for obj_ in obj.mro() if not is_ignore_type(obj_)]
    return res


if TYPE_CHECKING:
    from typing import Union as WithParents
else:
    class WithParents:
        def __class_getitem__(cls, item):
            parents = get_parents(item)
            if len(parents) > 1:
                return ProvideMultiple(parents)
            return item
