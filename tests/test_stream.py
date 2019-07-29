from binascii import unhexlify
from io import BytesIO

import pytest

from cbor2.encoder import CBOREncoder
from cbor2.stream import CBORWriter
from cbor2.types import CBORSimpleValue, FrozenDict


@pytest.mark.parametrize('value, expected', [
    (1000000, '1a000f4240'),
    (1.0e+300, 'fb7e37e43c8800759c'),
    (u'IETF', '6449455446'),
    (True, 'f5'),
    (CBORSimpleValue(19), 'f3')
])
def test_writer_simple(value, expected):
    fp = BytesIO()
    e = CBOREncoder(fp=fp)
    w = CBORWriter(encoder=e)
    w.write(value)
    assert fp.getvalue() == unhexlify(expected)


def _encode_value(wr, v, **kwargs):
    if isinstance(v, tuple):
        with wr.array(length=len(v), **kwargs) as a:
            for i in v:
                _encode_value(a, i)
    elif isinstance(v, list):
        with wr.array(length=None, **kwargs) as a:
            for i in v:
                _encode_value(a, i)
    elif isinstance(v, FrozenDict):
        with wr.map(length=len(v), **kwargs) as m:
            for k in sorted(v.keys()):
                _encode_value(m, v[k], key=k)
    elif isinstance(v, dict):
        with wr.map(length=None, **kwargs) as m:
            for k in sorted(v.keys()):
                _encode_value(m, v[k], key=k)
    else:
        wr.write(value=v, **kwargs)


@pytest.mark.parametrize('values, expected', [
    ((1,), '8101'),                                     # Fixed array
    ((1, 2, 3), '83010203'),                            # Fixed array
    ([1, 2, 3, 4], '9f01020304ff'),                     # Variable array
    ((1, (2, 3), (4, 5)), '8301820203820405'),          # Nested, fixed arrays
    ([1, [2, 3], [4, 5]], '9f019f0203ff9f0405ffff'),    # Nested, variable arrays
    ([1, (2, 3), (4, 5)], '9f01820203820405ff'),        # Nested, mixed arrays

    (FrozenDict(a=1), 'a1416101'),                      # Fixed map
    ({'a': 1}, 'bf416101ff'),                           # Variable map
    (FrozenDict(a=1, b=FrozenDict(c=2)), 'a24161014162a1416302'),  # Nested, fixed map
    ({'a': 1, 'b': {'c': 2}}, 'bf4161014162bf416302ffff'),  # Nested, variable map

    ({'a': (1, 2, 3)}, 'bf416183010203ff'),             # Variable map, fixed array
    ([1, 2, FrozenDict(a=1)], '9f0102a1416101ff'),      # Variable array, fixed map
])
def test_writer_container_success(values, expected):
    fp = BytesIO()
    e = CBOREncoder(fp=fp)
    w = CBORWriter(encoder=e)

    _encode_value(w, values)
    assert fp.getvalue() == unhexlify(expected)
