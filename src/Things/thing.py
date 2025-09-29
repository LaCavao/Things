from pydantic import BaseModel
from enum import Enum
from typing import get_origin, get_args, Union
from types import UnionType, NoneType
from .formats import FORMATS

class Thing(BaseModel):
    @classmethod
    def compile(cls, format='gbnf', as_str=True):
        if format not in FORMATS:
            raise ValueError(f"Unsupported format: {format}")
        
        templates = FORMATS[format]
        rules = {}
        
        def compile_type(type_hint, name=None, required=True):
            origin = get_origin(type_hint)
            args = get_args(type_hint)
            
            if type_hint in (str, int, float, bool):
                prim_name = type_hint.__name__
                if prim_name not in rules:
                    rules[prim_name] = templates['primitives'][prim_name]
                return prim_name
            
            if origin in (Union, UnionType) or isinstance(type_hint, UnionType):
                types = args if args else get_args(type_hint)
                non_none = [t for t in types if t is not NoneType]
                if len(non_none) == 1:
                    return compile_type(non_none[0], name, NoneType not in types)
                raise ValueError(f"Complex unions not supported: {type_hint}")
            
            if origin in (list, tuple):
                item_type = compile_type(args[0])
                list_name = f"{item_type}-arr"
                if list_name not in rules:
                    rules[list_name] = templates['list'].format(item=item_type)
                return list_name
            
            if isinstance(type_hint, type) and issubclass(type_hint, Enum):
                enum_name = type_hint.__name__.lower()
                if enum_name not in rules:
                    values = '|'.join(
                        templates['enum_value'].format(value=v) 
                        for v in type_hint._value2member_map_.keys()
                    )
                    rules[enum_name] = templates['enum'].format(
                        name=enum_name, 
                        values=values
                    )
                return enum_name
            
            if isinstance(type_hint, type) and issubclass(type_hint, Thing):
                nested_name = type_hint.__name__.lower()
                if nested_name not in rules:
                    compile_thing(type_hint)
                return nested_name
            
            raise ValueError(f"Unsupported type: {type_hint}")
        
        def compile_thing(thing_cls):
            class_name = thing_cls.__name__.lower()
            if class_name in rules:
                return
            
            # Reserve the name to prevent infinite recursion
            rules[class_name] = None
            
            fields = []
            for field_name, field_info in thing_cls.model_fields.items():
                field_type = field_info.annotation
                required = field_info.is_required()
                
                if isinstance(field_type, UnionType) and NoneType in get_args(field_type):
                    non_none = [t for t in get_args(field_type) if t is not NoneType]
                    field_type = non_none[0] if len(non_none) == 1 else Union[tuple(non_none)]
                    required = False
                
                type_name = compile_type(field_type, field_name, required)
                
                field_str = templates['field'].format(
                    name=field_name,
                    type=type_name,
                    optional='' if required else templates.get('optional', '')
                )
                fields.append(field_str)
            
            rules[class_name] = templates['object'].format(
                name=class_name,
                fields=templates['field_sep'].join(fields)
            )
        
        compile_thing(cls)
        
        if as_str:
            rule_strs = '\n'.join(rules.values())
            return templates['root'].format(name=cls.__name__.lower(), rules=rule_strs)
        
        return rules
    
    @classmethod
    def schema(cls, semantic=False):
        if not semantic:
            return super().model_json_schema()
        
        lines = []
        seen = set()
        to_process = []
        
        def format_type(type_hint):
            origin = get_origin(type_hint)
            args = get_args(type_hint)
            
            if type_hint in (str, int, float, bool):
                return type_hint.__name__
            
            if origin in (Union, UnionType) or isinstance(type_hint, UnionType):
                types = args if args else get_args(type_hint)
                non_none = [t for t in types if t is not NoneType]
                if NoneType in types and len(non_none) == 1:
                    return f"{format_type(non_none[0])} | None"
                return ' | '.join(format_type(t) for t in types)
            
            if origin in (list, tuple):
                inner = format_type(args[0])
                return f"{origin.__name__}[{inner}]"
            
            if isinstance(type_hint, type):
                return type_hint.__name__
            
            return str(type_hint).replace('typing.', '').replace('<class ', '').replace('>', '').replace("'", '')
        
        def collect_dependencies(type_hint, deps):
            origin = get_origin(type_hint)
            args = get_args(type_hint)
            
            if origin in (list, tuple) and args:
                collect_dependencies(args[0], deps)
            elif origin in (Union, UnionType) or isinstance(type_hint, UnionType):
                for t in (args if args else get_args(type_hint)):
                    if t is not NoneType:
                        collect_dependencies(t, deps)
            elif isinstance(type_hint, type) and issubclass(type_hint, (Thing, Enum)):
                if type_hint.__name__ not in seen:
                    deps.append(type_hint)
        
        def process_class(type_cls):
            if type_cls.__name__ in seen:
                return
            seen.add(type_cls.__name__)
            
            if issubclass(type_cls, Enum):
                lines.append(f"{type_cls.__name__} (ENUM):")
                for value in type_cls._value2member_map_.keys():
                    lines.append(f"    {value}")
            elif issubclass(type_cls, Thing):
                lines.append(f"{type_cls.__name__}:")
                deps = []
                for name, info in type_cls.model_fields.items():
                    type_str = format_type(info.annotation)
                    desc = f" ({info.description})" if info.description else ""
                    lines.append(f"    {name}: {type_str}{desc}")
                    collect_dependencies(info.annotation, deps)
                
                for dep in deps:
                    if dep not in to_process and dep.__name__ not in seen:
                        to_process.append(dep)
        
        process_class(cls)
        
        while to_process:
            next_type = to_process.pop(0)
            process_class(next_type)
        
        return '\n'.join(lines)