from .base import GrammarFormat

class GBNFFormat(GrammarFormat):
    def format_primitive(self, type_name: str) -> str:
        primitives = {
            'str': '''str ::= \"\\\"\"([0-9a-zA-Z.,;:!?()-@_'] | \" \")* \"\\\"\"''',
            'int': '''int ::= ("-"? ([0-9] | [1-9] [0-9]*))''',
            'float': '''float ::= ("-"? ([0-9] | [1-9] [0-9]*) ("." [0-9]+)?)''',
            'bool': '''bool ::= ("true" | "false")''',
        }
        return primitives[type_name]

    def format_list(self, item_rule: str) -> str:
        return f'''{item_rule}-arr ::= "[" ({item_rule} ("," {item_rule})*) "]"'''

    def format_enum(self, enum_name: str, enum_values: list[str]) -> str:
        mem_strs = '|'.join([f'"\\"{mem}\\""' for mem in enum_values])
        return f'''{enum_name.lower()} ::= ({mem_strs})'''

    def format_object(self, class_name: str, field_rules: list[str]) -> str:
        fields_str = "\",\"".join(field_rules)
        fields_str = f'({fields_str})'
        return f'{class_name.lower()} ::= "{{"{fields_str}"}}"'

    def format_field(self, name: str, rule: str, is_required: bool) -> str:
        optional = '?' if not is_required else ''
        return f'("\\"{name}\\"" ":" {rule}){optional}'

    def format_root(self, root_rule: str, all_rules: list[str]) -> str:
        joined_rules = '\n'.join(all_rules)
        return f'''root ::= {root_rule}
{joined_rules}'''