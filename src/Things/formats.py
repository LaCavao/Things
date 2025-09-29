FORMATS = {
    'gbnf': {
        'primitives': {
            'str': 'str ::= "\\"" ([0-9a-zA-Z.,;:!?()\\-@_\'] | " ")* "\\""',
            'int': 'int ::= ("-"? ([0-9] | [1-9] [0-9]*))',
            'float': 'float ::= ("-"? ([0-9] | [1-9] [0-9]*) ("." [0-9]+)?)',
            'bool': 'bool ::= ("true" | "false")',
        },
        'list': '{item}-arr ::= "[" ({item} ("," {item})*) "]"',
        'enum': '{name} ::= ({values})',
        'enum_value': '"\\"{value}\\""',
        'object': '{name} ::= "{{" {fields} "}}"',
        'field': '("\\"{name}\\"" ":" {type}){optional}',
        'field_sep': '","',
        'optional': '?',
        'root': 'root ::= {name}\n{rules}',
    },
    'ebnf': {
        'primitives': {
            'str': 'STRING',
            'int': 'INT',
            'float': 'FLOAT', 
            'bool': 'BOOL',
        },
        'list': '{item}_LIST',
        'enum': '{name}',
        'enum_value': '"{value}"',
        'object': '{name}',
        'field': '\\"{name}\\" ":" {type}',
        'field_sep': ' "," ',
        'optional': '',
        'root': '{rules}\n\nSTRING: "\\"" (/[^"\\\\]/ | "\\\\" .)* "\\""\nINT: [+-]?[0-9]+\nFLOAT: [+-]?[0-9]+\\.[0-9]+([eE][+-]?[0-9]+)?\nBOOL: "true" | "false"',
        'rules': {
            'STRING': 'STRING: "\\"" (/[^"\\\\]/ | "\\\\" .)* "\\""',
            'INT': 'INT: [+-]?[0-9]+',
            'FLOAT': r'FLOAT: [+-]?[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?',
            'BOOL': 'BOOL: "true" | "false"',
        }
    }
}