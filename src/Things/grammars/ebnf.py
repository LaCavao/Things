from .base import GrammarFormat

# TODO - Complete/verify this is valid EBNF.
# I only did this as a test of the new base GrammarFormat, so not critical rn.
# Most of my use is GBNF (.gguf llama models), but I want to make sure the base is generic.

class EBNFFormat(GrammarFormat):
    def __init__(self):
        self.rules = {}

    def format_primitive(self, type_name: str) -> str:
        primitives = {
            'str': 'STRING: "\\"" (/[^"\\\\]/ | "\\\\" .)* "\\""',
            'int': 'INT: [+-]?[0-9]+',
            'float': r'FLOAT: [+-]?[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?',
            'bool': 'BOOL: "true" | "false"'
        }
        rule = primitives[type_name]
        self.rules[type_name.upper()] = rule
        return type_name.upper()

    def format_list(self, item_rule: str) -> str:
        rule_name = f'{item_rule.upper()}_LIST'
        self.rules[rule_name] = f'{rule_name.upper()}: "[" ({item_rule.upper()} ("," {item_rule.upper()})*)? "]"'
        return rule_name

    def format_enum(self, enum_name: str, enum_values: list[str]) -> str:
        values = ' | '.join([f'"{value}"' for value in enum_values])
        self.rules[enum_name.upper()] = f'{enum_name.upper()}: {values}'
        return enum_name.upper()

    def format_object(self, class_name: str, field_rules: list[str]) -> str:
        fields = ' ","? '.join(field_rules)
        self.rules[class_name.upper()] = f'{class_name.upper()}: "{{" ({fields})? "}}"'
        return class_name.upper()

    def format_field(self, name: str, rule: str, is_required: bool) -> str:
        if is_required:
            return f'"\\"" "{name}" "\\"" ":" {rule}'
        else:
            field_rule = f'{name.upper()}_FIELD'
            self.rules[field_rule] = f'{field_rule}: "\\"" "{name}" "\\"" ":" {rule}'
            return field_rule + '?'

    def format_root(self, root_rule: str, all_rules: list[str]) -> str:
        root = f'?start: {root_rule}\n\n'
        rules = '\n'.join(self.rules.values())
        return root + rules