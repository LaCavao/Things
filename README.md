# Things

Everything's a Thing

Automatically convert Pydantic models into schemas:

- GBNF grammars for constrained sampling in llama.cpp
    - Easy extension to other grammar formats by providing type rules...
    - ...see the EBNF example (haven't evaluated these outside GBNF)
- Semantic schemas for use in prompting (including field descriptions where provided)

This module is minimaln; it doesn't touch the inference process, and that is very intentional.
It is purely concerned with the representation of data.

## Usage

```python
from things import Thing
from pydantic import Field

# Automatically a Pydantic BaseModel
# Use of Field isn't necessary unless you want to add descriptions or optional fields
class Student(Thing):
    name: str = Field(description="First and last name of the student")
    age: int = Field(description="Age of the student, in years")

# Prints a string 
print(Student.schema(semantic=True))
"""
Student:
    name: str (First and last name of the student)
    age: int (Age of the student, in years)
"""

# Prints a GBNF grammar
print(Student.grammar(format='gbnf', as_str=True))
"""
root ::= student
str ::= "\""([0-9a-zA-Z.,;:!?()-@_'] | " ")* "\""
int ::= ("-"? ([0-9] | [1-9] [0-9]*))
student ::= "{"(("\"name\"" ":" str)","("\"age\"" ":" int))"}"
"""
```

Handles lists, enums, and nested Thing dependencies.

```python
from things import Thing
from pydantic import Field
from enum import Enum

class Subject(Enum):
    MATH = "math"
    HISTORY = "history"
    SCIENCE = "science"

class Student(Thing):
    name: str = Field(description="First and last name of the student")
    age: int = Field(description="Age of the student, in years")

class Professor(Thing):
    name: str = Field(description="First and last name of the professor")
    subject: Subject = Field(description="Subject the professor teaches")
    students: list[Student] = Field(description="Students the professor teaches")

# Prints the schema for Professor, as well as its dependencies
print(Professor.schema(semantic=True))
"""
Subject (ENUM):
    math
    history
    science
Student:
    name: str (First and last name of the student)
    age: int (Age of the student, in years)
Professor:
    name: str (First and last name of the professor)
    subject: Subject (Subject the professor teaches)
    students: list[Student] (Students the professor teaches)
"""

print(Professor.grammar(format='gbnf', as_str=True))
"""
root ::= professor
str ::= "\""([0-9a-zA-Z.,;:!?()-@_'] | " ")* "\""
subject ::= ("\"math\""|"\"history\""|"\"science\"")
int ::= ("-"? ([0-9] | [1-9] [0-9]*))
student ::= "{"(("\"name\"" ":" str)","("\"age\"" ":" int))"}"
student-arr ::= "[" (student ("," student)*) "]"
professor ::= "{"(("\"name\"" ":" str)","("\"subject\"" ":" subject)","("\"students\"" ":" student-arr))"}"
"""
```

### NOTE
You can make fields are optional using default "None" in the Field

```python
from pydantic import Field

class Example(Thing):
    baz: str = Field(default=None) # Yes
    bam: str | None = Field(default=None) # Yes
    foo: str | None # No!
    bar: Optional[str] # No!
```

### BUGS / TODO

- Optional fields that aren't generated during inference will wind up leaving a leading comma in the generated result; trivial to strip out of the output string, but needs to be fixed at the grammar level