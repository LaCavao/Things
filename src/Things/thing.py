from pydantic import BaseModel, Field
from enum import Enum
from typing import get_origin, get_args, Union, Any, Callable
from types import UnionType, NoneType
from .type_wrapper import TypeWrapper
from .grammars.base import GrammarFormat
from .grammars.gbnf import GBNFFormat
from .grammars.ebnf import EBNFFormat

class GrammarBuilder:
    _PRIMITIVES = {
        str: lambda f: f.format_primitive('str'),
        int: lambda f: f.format_primitive('int'),
        float: lambda f: f.format_primitive('float'),
        bool: lambda f: f.format_primitive('bool'),
    }

    @classmethod
    def from_type(cls, type_wrapper: 'TypeWrapper', format: GrammarFormat, grammars: dict = None):
        if grammars is None:
            grammars = {}
        if type_wrapper.vanilla_type in cls._PRIMITIVES:
            rule = cls._PRIMITIVES[type_wrapper.vanilla_type](format)
            grammars[type_wrapper.vanilla_type.__name__] = rule
            return [type_wrapper.vanilla_type.__name__]
        elif issubclass(type_wrapper.vanilla_type, Thing):
            rule = type_wrapper.vanilla_type.grammar(format=format, grammars=grammars)[type_wrapper.vanilla_type.__name__.lower()]
            grammars[type_wrapper.vanilla_type.__name__.lower()] = rule
            return [type_wrapper.vanilla_type.__name__.lower()]
        elif type_wrapper.origin in (list, tuple):
            return cls._list_grammar(type_wrapper, format, grammars)
        elif issubclass(type_wrapper.vanilla_type, Enum):
            return [cls._enum_grammar(type_wrapper, format, grammars)]
        else:
            raise ValueError(f'Unsupported type: {type_wrapper}')

    @classmethod
    def _list_grammar(cls, type_wrapper: 'TypeWrapper', format: GrammarFormat, grammars: dict) -> list[str]:
        if len(type_wrapper.args) != 1:
            raise ValueError(f'List type {type_wrapper} should have exactly one argument')

        member = TypeWrapper(type_wrapper.args[0], get_origin(type_wrapper.args[0]), get_args(type_wrapper.args[0]), True)
        mem_rules = cls.from_type(member, format, grammars=grammars)
        if isinstance(mem_rules, str):
            mem_rules = [mem_rules]

        rule_name = f'{mem_rules[0]}-arr'

        if rule_name not in grammars:
            grammars[rule_name] = format.format_list(mem_rules[0])

        return [rule_name] + mem_rules

    @classmethod
    def _enum_grammar(cls, type_wrapper: 'TypeWrapper', format: GrammarFormat, grammars: dict) -> str:
        members = type_wrapper.vanilla_type._value2member_map_.keys()
        grammar_handle = type_wrapper.vanilla_type.__name__.lower()
        if grammar_handle not in grammars:
            grammars[grammar_handle] = format.format_enum(type_wrapper.vanilla_type.__name__, members)
        return grammar_handle

class Thing:
    @classmethod
    def schema(cls, semantic: bool = False):
        if not issubclass(cls, BaseModel):
            raise ValueError(f'Thing {cls} is not a Pydantic BaseModel')

        fields = cls.model_fields
        if not semantic:
            return {name: TypeWrapper.from_field_info(field_info) for name, field_info in fields.items()}

        schema_parts = []
        processed_types = set()

        def process_type(current_type):
            if current_type.__name__ in processed_types:
                return
            processed_types.add(current_type.__name__)

            if issubclass(current_type, Enum):
                enum_values = [f"    {value}" for value in current_type._value2member_map_.keys()]
                schema_parts.append(f"{current_type.__name__} (ENUM):\n" + "\n".join(enum_values))
            elif issubclass(current_type, Thing):
                class_schema = []
                for field_name, field_info in current_type.model_fields.items():
                    tw = TypeWrapper.from_field_info(field_info)
                    description = f" ({field_info.description})" if field_info.description else ""
                    class_schema.append(f"    {field_name}: {tw.type_str()}{description}")

                    cls._process_nested_types(tw, process_type)

                schema_parts.append(f"{current_type.__name__}:\n" + "\n".join(class_schema))

        process_type(cls)
        return "\n".join(schema_parts)

    @staticmethod
    def _process_nested_types(tw, process_func):
        if isinstance(tw.vanilla_type, UnionType):
            for arg in tw.args:
                if issubclass(arg, (Thing, Enum)):
                    process_func(arg)
        elif issubclass(tw.vanilla_type, (Thing, Enum)):
            process_func(tw.vanilla_type)

    @classmethod
    def grammar(cls, format: str | GrammarFormat = 'gbnf', grammars: dict = None, as_str: bool = False):
        fields = cls.schema()
        field_rules = []

        gen_grammars = {} if grammars is None else grammars

        if isinstance(format, str):
            if format == 'gbnf':
                format_obj = GBNFFormat()
            # elif format == 'ebnf': TODO fix
            #     format_obj = EBNFFormat()
            else:
                raise ValueError(f"Unsupported grammar format string: {format}")
        elif isinstance(format, GrammarFormat):
            format_obj = format
        else:
            raise ValueError(f"Invalid format type: {type(format)}. Expected str or GrammarFormat.")

        for name, type_wrapper in fields.items():
            rules = GrammarBuilder.from_type(type_wrapper, format_obj, grammars=gen_grammars)
            if isinstance(rules, str):
                rules = [rules]
                
            field_rules.append(format_obj.format_field(name, rules[0], type_wrapper.is_required))

        cls_rule = format_obj.format_object(cls.__name__, field_rules)
        gen_grammars[cls.__name__.lower()] = cls_rule

        if as_str:
            return format_obj.format_root(cls.__name__.lower(), list(gen_grammars.values()))

        return gen_grammars