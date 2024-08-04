from abc import ABC
from typing import Annotated, Any, Generic, Protocol, TypeVar

import pytest

from dishka import (
    DEFAULT_COMPONENT,
    FromComponent,
    Provider,
    Scope,
    make_container,
)
from dishka._adaptix.feature_requirement import HAS_PY_311
from dishka.entities.with_parents import WithParents
from dishka.exceptions import NoFactoryError

if HAS_PY_311:
    from typing import TypeVarTuple, Unpack

    Ts = TypeVarTuple("TS")  # noqa: PLC0132

T = TypeVar("T")
B = TypeVar("B")


def test_simple_inheritance() -> None:
    class A1: ...
    class A2(A1): ...
    class A3(A2): ...

    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: A3(), provides=WithParents[A3])
    container = make_container(provider)
    assert (
        container.get(A3)
        is container.get(A2)
        is container.get(A1)
    )


@pytest.mark.parametrize(
    ("obj", "value", "component"),
    [
        (type("A1", (Protocol,), {}), Protocol, DEFAULT_COMPONENT),
        (type("A2", (object,), {}), object, DEFAULT_COMPONENT),
        (type("A3", (ABC,), {}), ABC, DEFAULT_COMPONENT),
        (type("A3", (ABC,), {}), ABC, "TTT"),
    ],
)
def test_ignore_parent_type(obj: Any, value: Any, component: Any) -> None:
    provider = Provider(scope=Scope.APP, component=component)
    provider.provide(
        source=lambda: obj(),
        provides=Annotated[WithParents[obj], FromComponent(component)],
    )
    container = make_container(provider)

    try:
        container.get(value, component=component)
    except NoFactoryError:
        pass
    else:
        raise AssertionError



def test_type_var() -> None:
    class A1(Generic[T]): ...
    class A2(A1[str]): ...

    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: A2(), provides=WithParents[A2])

    container = make_container(provider)

    assert(
        container.get(A2)
        is container.get(A1[str])
    )


@pytest.mark.skipif(
    not HAS_PY_311,
    reason="test for python >= 3.11",
)
def test_type_var_tuple() -> None:
    class A1(Generic[Unpack[Ts]]): ...
    class A2(A1[str, int, type]): ...

    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: A2(), provides=WithParents[A2])

    container = make_container(provider)

    assert (
        container.get(A2)
        is container.get(A1[str, int, type])
    )

if HAS_PY_311:
    class A1(Generic[T, Unpack[Ts]]): ...
    class A2(A1[str, int, type], int): ...

    class B1(Generic[Unpack[Ts], T], int): ...
    class B2(B1[int, tuple[str, ...], type], int): ...

    class C1(Generic[B, Unpack[Ts], T]): ...
    class C2(C1[int, type, str, tuple[str, ...]], int): ...

    params = [
        (A2, A1[str, int, type], int),
        (B2, B1[int, tuple[str, ...], type], int),
        (C2, C1[int, type, str, tuple[str, ...]], int),
    ]
else:
    params = []

@pytest.mark.parametrize(
    ("obj", "val1", "val2"),
    params,
)
@pytest.mark.skipif(
    not HAS_PY_311,
reason="test for python >= 3.11",
)
def test_type_var_and_type_var_tuple(
    obj: Any,
    val1: Any,
    val2: Any,
) -> None:
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: obj(), provides=WithParents[obj])
    container = make_container(provider)

    assert (
        container.get(obj)
        is container.get(val1)
        is container.get(val2)
    )

def test_deep_inheritance() -> None:
    class A1(Generic[T], float): ...
    class A2(A1[T], Generic[T]): ...

    class B1: ...
    class B2(B1): ...
    class B3(B2): ...

    class C1(Generic[T], B3): ...
    class D1(A2[int], C1[str]): ...

    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: D1(), provides=WithParents[D1])
    container = make_container(provider)

    assert(
        container.get(D1)
        is container.get(A2[int])
        is container.get(A1[int])
        is container.get(float)
        is container.get(C1[str])
        is container.get(B3)
        is container.get(B2)
        is container.get(B1)
        is container.get(D1)
    )
