from numbers import Integral

from .encoder import (
    encode_length,
    encode_indefinite,
    encode_break
)


class CBORWriterError(Exception):
    """
    Raised whenever CBORWriter, CBORArrayWriter or CBORMapWriter encounter a
    runtime error.
    """
    pass


class _CBORWriterBase(object):
    __slots__ = ('encoder',)

    def __init__(self, encoder):
        self.encoder = encoder

    def _array_context_mgr(self, length=None):
        return _CBORContainerWriterContextManager(
            self.encoder,
            0x80, length,
            CBORArrayWriter(self.encoder, length=length)
        )

    def _map_context_mgr(self, length=None):
        return _CBORContainerWriterContextManager(
            self.encoder,
            0xA0, length,
            CBORMapWriter(self.encoder, length=length)
        )


class _CBORContainerWriterContextManager(object):
    __slots__ = ('encoder', 'writer', 'major_tag', 'length',)

    def __init__(self, encoder, major_tag, length, writer):
        if not(length is None or isinstance(length, Integral)):
            raise ValueError(
                'Length can be either a positive integral value or None')

        if length is not None and length < 0:
            raise ValueError(
                'Length can be either a positive integral value or None')

        self.encoder = encoder
        self.writer = writer
        self.major_tag = major_tag
        self.length = length

    def __enter__(self):
        if self.length is None:
            # Indefinite length
            encode_indefinite(self.encoder, self.major_tag)
        else:
            self.encoder.write(encode_length(self.major_tag, self.length))

        return self.writer

    def __exit__(self, *args, **kwargs):
        if self.length is None:
            encode_break(self.encoder)
        else:
            if self.writer.capacity > 0:
                raise CBORWriterError(
                    'Insufficient number of values written out')


class CBORArrayWriter(_CBORWriterBase):
    """
    A writer object for writing out array values. For fixed-length arrays, it
    checks whether the required count has been exceeded and raises an exception
    in that case.
    """
    __slots__ = ('capacity',)

    def __init__(self, encoder, length):
        super(CBORArrayWriter, self).__init__(encoder)
        self.capacity = length

    def _commit_element(self):
        if self.capacity is not None:
            if self.capacity <= 0:
                raise CBORWriterError("Exceeded the requested array element count")

            self.capacity -= 1

    def array(self, length=None):
        """
        Write an array using a context block.
        :param length: The expected length of the array. If None, then the array
            is of an indefinite length and any number of values can be added.
        """
        self._commit_element()
        return self._array_context_mgr(length)

    def map(self, length=None):
        """
        Write a map using a context block.
        :param length: The expected number of key/value pairs in the map.
            If None, then the map is of an indefinite length and any number of
            key/value pairs can be added.
        """
        self._commit_element()
        return self._map_context_mgr(length)

    def write(self, value):
        """
        Write a single value to the stream. If the current array is of a fixed
        length, then this function also checks that the appropriate number of
        values has been written out, and raises an exception if this number is
        exceeded. The remaining count can be read through the ``capacity``
        property.
        :param value: The value to write out. The value can be any object that
        the ``cbor2`` library can translate to a CBOR-encoded value.
        """
        self._commit_element()
        self.encoder.encode(value)


class CBORMapWriter(_CBORWriterBase):
    """
    A writer object for writing out key-value pairs to a map. For fixed-length maps, it
    checks whether the required count has been exceeded and raises an exception in
    that case.
    """
    __slots__ = ('capacity',)

    def __init__(self, encoder, length):
        super(CBORMapWriter, self).__init__(encoder)
        self.capacity = length

    def _commit_element(self):
        if self.capacity is not None:
            if not self.capacity:
                raise CBORWriterError("Exceeded the requested map element count")

            self.capacity -= 1

    def array(self, key, length=None):
        """
        Write an array using a context block, associated with the given key in
        the current map.
        :param key: The key to store the new array under in the current map.
        :param length: The expected length of the array. If None, then the array
            is of an indefinite length and any number of values can be added.
        """
        self._commit_element()
        self.encoder.encode(key)
        return self._array_context_mgr(length)

    def map(self, key, length=None):
        """
        Write a map using a context block, associated with the given key in
        the current map.
        :param key: The key to store the new map under in the current map.
        :param length: The expected number of key/value pairs in the map.
            If None, then the map is of an indefinite length and any number of
            key/value pairs can be added.
        """
        self._commit_element()
        self.encoder.encode(key)
        return self._map_context_mgr(length)

    def write(self, key, value):
        """
        Write a single key/value pair to the stream. If the current array is of
        a fixed length, then this function also checks that the appropriate
        number of pairs has been written out, and raises an exception if this
        number is exceeded. The remaining count can be read through the
        ``capacity`` property.
        :param key: The key to store the value under in the current map.
        :param value: The value to store for the given key.
        """
        self._commit_element()
        self.encoder.encode(key)
        self.encoder.encode(value)


class CBORWriter(_CBORWriterBase):
    """
    A writer object used for encoding python objects as a stream of CBOR data.
    """
    __slots__ = ()

    def __init__(self, encoder):
        super(CBORWriter, self).__init__(encoder)

    def array(self, length=None):
        """
        Write an array using a context block.
        :param length: The expected length of the array. If None, then the array
            is of an indefinite length and any number of values can be added.
        """
        return self._array_context_mgr(length)

    def map(self, length=None):
        """
        Write a map using a context block.
        :param length: The expected number of key/value pairs in the map.
            If None, then the map is of an indefinite length and any number of
            key/value pairs can be added.
        """
        return self._map_context_mgr(length)

    def write(self, value):
        """
        Write a single value to the stream.
        :param value: The value to encode and write out to the stream.
        """
        self.encoder.encode(value)
