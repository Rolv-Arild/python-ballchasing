"""Base classes and the @model decorator for the typed response objects (see models.py)."""
import functools
import logging
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime
from typing import get_args

try:
    from typing import dataclass_transform
except ImportError:  # Python 3.10
    def dataclass_transform(**kwargs):
        return lambda fn: fn

from ballchasing.util.dates import from_rfc3339, to_rfc3339

logger = logging.getLogger("ballchasing")

_reported_unknown_fields: set[tuple[str, str]] = set()


@dataclass_transform(field_specifiers=(field,))
def model(cls=None, /, **dataclass_kwargs):
    """
    Like ``@dataclass`` (and taking the same arguments), but the generated ``__init__`` accepts keyword arguments
    that are not fields.

    The API adds response fields over time; a plain dataclass would raise a ``TypeError`` on the first unknown one.
    Unknown fields are kept (unconverted) in the instance's ``_extra`` dict instead, and included by ``to_dict``.
    """
    if cls is None:
        return functools.partial(model, **dataclass_kwargs)
    cls = dataclass(cls, **dataclass_kwargs)
    dataclass_init = cls.__init__
    known = frozenset(f.name for f in fields(cls))

    @functools.wraps(dataclass_init)
    def __init__(self, *args, **kwargs):
        extra = {k: kwargs.pop(k) for k in [k for k in kwargs if k not in known]}
        for k in extra:
            if (cls.__name__, k) not in _reported_unknown_fields:
                _reported_unknown_fields.add((cls.__name__, k))
                logger.debug(f"Unknown field '{k}' for {cls.__name__}, stored in _extra")
        self._extra = extra
        dataclass_init(self, *args, **kwargs)

    cls.__init__ = __init__
    return cls


class _BaseModel:
    """
    Base model class for all dataclasses in this module.
    """
    _extra: dict  # Response fields without a dataclass field (set by @model), not a dataclass field itself

    def to_dict(self):
        """
        Convert (back) to a dict. Not a perfect recreation.
        """
        result = dict(getattr(self, "_extra", {}))
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, _BaseModel):
                result[field.name] = value.to_dict()
            elif isinstance(value, list):
                if len(value) > 0:
                    result[field.name] = [item.to_dict() if isinstance(item, _BaseModel) else item for item in value]
            elif isinstance(value, datetime):
                # Convert datetime objects to rfc3339 formatted strings
                result[field.name] = to_rfc3339(value)
            elif value is not None:
                # Include non-None values, preserving valid 0 and False values
                result[field.name] = value
        return result


class _DictToTypeMixin:
    """
    Mixin class to convert dicts to their respective types in dataclasses.
    """

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            actual_type = field.type
            if args := get_args(field.type):
                actual_type = args[0]
            # Into models and other dataclasses (e.g. in a user's subclass), not e.g. Any or dict
            is_model = isinstance(actual_type, type) and (issubclass(actual_type, _BaseModel) or is_dataclass(actual_type))
            if isinstance(value, dict) and is_model:
                new_value = actual_type(**value)
                setattr(self, field.name, new_value)
            elif isinstance(value, list) and is_model:
                new_value = [actual_type(**item) if isinstance(item, dict) else item for item in value]
                setattr(self, field.name, new_value)
            elif isinstance(value, str) and actual_type is datetime:
                # Load rfc3339 formatted strings as datetime objects
                new_value = from_rfc3339(value)
                setattr(self, field.name, new_value)
            # else:  # For testing
            #     # Check that the value has the type specified in the dataclass field
            #     if value is not None and not isinstance(value, actual_type):
            #         if isinstance(value, int) and actual_type is float:
            #             pass  # ints can be converted losslessly to floats
            #         else:
            #             raise TypeError(f"Expected {field.name} to be of type {actual_type}, got {type(value)}")
