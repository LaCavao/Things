from enum import Enum
from typing import get_origin, get_args, Union, Any, Callable
from types import UnionType, NoneType
from pydantic.fields import FieldInfo, PydanticUndefined

class TypeWrapper:
    vanilla_type: type
    origin: type | None
    args: tuple[type] | None
    is_required: bool

    def __init__(self, vanilla_type, origin, args, is_required):
        self.vanilla_type = vanilla_type
        self.origin = origin
        self.args = args
        self.is_required = is_required

    def __repr__(self):
        return f'TypeWrapper(vanilla_type={self.vanilla_type}, origin={self.origin}, args={self.args}, is_required={self.is_required})'

    def type_str(self):
        if isinstance(self.vanilla_type, UnionType) or self.origin is Union:
            types = self.args if self.args else get_args(self.vanilla_type)
            non_none_types = [t for t in types if t is not NoneType]
            
            if len(non_none_types) == 1:
                base_type_str = self._type_name(non_none_types[0])
            else:
                base_type_str = ' | '.join(self._type_name(t) for t in non_none_types)
            
            return f'{base_type_str} | None' if NoneType in types else base_type_str
        else:
            base_type_str = self._base_type_str()
            return base_type_str if self.is_required else f'{base_type_str} | None'

    def _base_type_str(self):
        if self.origin is None:
            return self._type_name(self.vanilla_type)
        elif self.origin in (list, tuple):
            inner_type = TypeWrapper(self.args[0], get_origin(self.args[0]), get_args(self.args[0]), True)._base_type_str()
            return f"{self.origin.__name__}[{inner_type}]"
        else:
            return f"{self.origin.__name__}[{','.join([TypeWrapper(arg, get_origin(arg), get_args(arg), True)._base_type_str() for arg in self.args])}]"
    
    @staticmethod
    def _type_name(t):
        return t.__name__ if hasattr(t, '__name__') else str(t)

    @classmethod
    def from_field_info(cls, field_info: FieldInfo):
        field_t = field_info.annotation
        field_required = field_info.is_required()

        if isinstance(field_t, UnionType):
            field_t, field_required = cls._process_union_type(field_t, field_info)

        return cls(field_t, get_origin(field_t), get_args(field_t), field_required)

    @staticmethod
    def _process_union_type(field_t, field_info):
        if NoneType in get_args(field_t):
            if field_info.default is PydanticUndefined:
                raise ValueError(f'Field {field_info.name} has no default value but is optionally None. Set a default value of None if this is intentional.')
            
            non_none_types = [t for t in get_args(field_t) if t is not NoneType]
            field_t = non_none_types[0] if len(non_none_types) == 1 else Union[tuple(non_none_types)]
            field_required = False
        else:
            field_required = field_info.is_required()

        return field_t, field_required
