from abc import ABC, abstractmethod

class GrammarFormat(ABC):
    @abstractmethod
    def format_primitive(self, type_name: str) -> str:
        pass

    @abstractmethod
    def format_list(self, item_rule: str) -> str:
        pass

    @abstractmethod
    def format_enum(self, enum_name: str, enum_values: list[str]) -> str:
        pass

    @abstractmethod
    def format_object(self, class_name: str, field_rules: list[str]) -> str:
        pass

    @abstractmethod
    def format_field(self, name: str, rule: str, is_required: bool) -> str:
        pass

    @abstractmethod
    def format_root(self, root_rule: str, all_rules: list[str]) -> str:
        pass