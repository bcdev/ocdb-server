from abc import ABCMeta, abstractmethod
from typing import List, Optional, Any, TypeVar, Generic, Union, Sequence

KW_AND = 'AND'
KW_OR = 'OR'
KW_NOT = 'NOT'
KEYWORDS = {KW_AND, KW_OR, KW_NOT}

OP_INCLUDE = '+'
OP_EXCLUDE = '-'
OPERATORS = {OP_INCLUDE, OP_EXCLUDE}

Value = Union[str, bool, int, float, None]


class Query(metaclass=ABCMeta):
    """
    Interface to be implemented by all query terms.

    * QTList - same as
    """

    @abstractmethod
    def accept(self, visitor: 'QueryVisitor') -> Any:
        pass

    @abstractmethod
    def op_precedence(self) -> int:
        return False

    def is_of_same_type(self, other: Any):
        return type(self) is type(other)

    @abstractmethod
    def args_to_repr(self) -> str:
        """ Get Python representation of constructor args."""

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.args_to_repr()})'


class PhraseQuery(Query):
    def __init__(self, terms: Sequence[Query]):
        self.terms = tuple(terms)

    def __eq__(self, other) -> bool:
        return self.is_of_same_type(other) and self.terms == other.terms

    def __str__(self) -> str:
        return ' '.join(map(str, self.terms))

    def args_to_repr(self) -> str:
        args = ', '.join(map(repr, self.terms))
        return f'[{args}]'

    def accept(self, visitor: 'QueryVisitor') -> Any:
        return visitor.visit_phrase(self, [term.accept(visitor) for term in self.terms])

    def op_precedence(self) -> int:
        return 400


class BinaryOpQuery(Query):
    def __init__(self, op: str, term1: Query, term2: Query):
        self.op = op
        self.term1 = term1
        self.term2 = term2

    def __eq__(self, other):
        return self.is_of_same_type(other) \
               and self.op == other.op \
               and self.term1 == other.term1 \
               and self.term2 == other.term2

    def __str__(self) -> str:
        t1 = str(self.term1)
        t2 = str(self.term2)
        if self.op_precedence() > self.term1.op_precedence():
            t1 = f'({t1})'
        if self.op_precedence() > self.term2.op_precedence():
            t2 = f'({t2})'
        return f'{t1} {self.op} {t2}'

    def args_to_repr(self) -> str:
        t1 = repr(self.term1)
        t2 = repr(self.term2)
        return f'"{self.op}", {t1}, {t2}'

    def accept(self, visitor: 'QueryVisitor') -> Any:
        return visitor.visit_binary_op(self, self.term1.accept(visitor), self.term2.accept(visitor))

    def op_precedence(self) -> int:
        if self.op == KW_OR:
            return 500
        else:
            return 600


class UnaryOpQuery(Query):
    def __init__(self, op: str, term: Query):
        self.op = op
        self.term = term

    def __eq__(self, other) -> bool:
        return self.is_of_same_type(other) \
               and self.op == other.op \
               and self.term == other.term

    def __str__(self) -> str:
        term = str(self.term)
        if self.op_precedence() > self.term.op_precedence():
            term = f'({term})'
        if self.op in KEYWORDS:
            return f'{self.op} {term}'
        else:
            return f'{self.op}{term}'

    def args_to_repr(self) -> str:
        return f'"{self.op}", {repr(self.term)}'

    def accept(self, visitor: 'QueryVisitor') -> Any:
        return visitor.visit_unary_op(self, self.term.accept(visitor))

    def op_precedence(self) -> int:
        if self.op == KW_NOT:
            return 800
        else:
            return 900


class FieldQuery(Query, metaclass=ABCMeta):
    def __init__(self, name: Optional[str]):
        self.name = name

    def op_precedence(self) -> int:
        return 1000

    @abstractmethod
    def value_to_str(self):
        """ Turn value into string. """

    def __str__(self) -> str:
        value = self.value_to_str()
        return f'{self.name}:{value}' if self.name else value

    @abstractmethod
    def value_args_to_repr(self):
        """ Turn value(s) into Python representation. """

    def args_to_repr(self) -> str:
        args = self.value_args_to_repr()
        return f'"{self.name}", {args}' if self.name else f'None, {args}'


class FieldValueQuery(FieldQuery):
    @classmethod
    def is_text(cls, value: Value):
        return isinstance(value, str)

    def __init__(self, name: Optional[str], value: Value):
        super().__init__(name)
        self.value = value

    def __eq__(self, other):
        return self.is_of_same_type(other) \
               and self.name == other.name \
               and self.value == other.value

    def value_to_str(self):
        return '"' + self.value.replace('"', '\\"') + '"' \
            if self._is_quoted_text() else str(self.value)

    def value_args_to_repr(self):
        return '"' + self.value.replace('"', '\\"') + '"' \
            if isinstance(self.value, str) else repr(self.value)

    def accept(self, visitor: 'QueryVisitor') -> Any:
        return visitor.visit_field_value(self)

    def op_precedence(self) -> int:
        return 1000

    def _is_text(self):
        return self.is_text(self.value)

    def _is_quoted_text(self) -> bool:
        return self._is_text() \
               and any(map(lambda c: c in ' +-&|!(){}[]^"~*?:\\', self.value))


class FieldWildcardQuery(FieldValueQuery):

    @classmethod
    def is_wildcard_text(cls, value: Value) -> bool:

        if not cls.is_text(value):
            return False

        escape = False
        wildcard_char_seen = False
        for i in range(len(value)):
            c = value[i]
            if c == '\\':
                escape = True
            elif not escape and c == '?' or c == '*':
                wildcard_char_seen = True
            elif not escape and c.isspace():
                return False
            else:
                escape = False

        return wildcard_char_seen

    def __init__(self, name: Optional[str], value: str):
        super().__init__(name, value)
        assert isinstance(value, str)

    def accept(self, visitor: 'QueryVisitor') -> Any:
        return visitor.visit_field_wildcard(self)

    def _is_quoted_text(self) -> bool:
        return False


class FieldRangeQuery(FieldQuery):

    def __init__(self, name: Optional[str], start_value: Value, end_value: Value, is_exclusive=False):
        super().__init__(name)
        assert not (start_value is None and end_value is None)
        self.start_value = start_value
        self.end_value = end_value
        self.is_exclusive = is_exclusive

    def __eq__(self, other):
        return self.is_of_same_type(other) \
               and self.name == other.name \
               and self.start_value == other.start_value \
               and self.end_value == other.end_value \
               and self.is_exclusive == other.is_exclusive

    def value_to_str(self):
        v = f'{self.start_value} TO {self.end_value}'
        if self.is_exclusive:
            v = '{' + v + '}'
        else:
            v = '[' + v + ']'
        return v

    def value_args_to_repr(self):
        args = f'{self.start_value}, {self.end_value}'
        if self.is_exclusive:
            args += f', is_exclusive={self.is_exclusive}'
        return args

    def accept(self, visitor: 'QueryVisitor') -> Any:
        return visitor.visit_field_range(self)


T = TypeVar('T')


class QueryVisitor(Generic[T], metaclass=ABCMeta):
    """ Visitor used to visit all nodes of a Query tree. """

    @abstractmethod
    def visit_phrase(self, qt: PhraseQuery, terms: List[T]) -> Optional[T]:
        """
        Visit a PhraseQuery query term and compute an optional result.
        :param qt: The PhraseQuery query term to be visited.
        :param terms: The results of the list elements' visit.
        :return: The optional result of the visit.
        """

    @abstractmethod
    def visit_binary_op(self, qt: BinaryOpQuery, term1: T, term2: T) -> Optional[T]:
        """
        Visit a BinaryOpQuery query term and compute an optional result.
        :param qt: The BinaryOpQuery query term to be visited.
        :param term1: The result of the first operand's visit.
        :param term2: The result of the second operand's visit.
        :return: The optional result of the visit.
        """

    @abstractmethod
    def visit_unary_op(self, qt: UnaryOpQuery, term: T) -> Optional[T]:
        """
        Visit a UnaryOpQuery query term and compute an optional result.
        :param qt: The UnaryOpQuery query term to be visited.
        :param term: The result of the unary operand's visit.
        :return: The optional result of the visit.
        """

    @abstractmethod
    def visit_field_value(self, qt: FieldValueQuery) -> Optional[T]:
        """
        Visit a FieldValueQuery query term and compute an optional result.
        :param qt: The FieldValueQuery query term to be visited.
        :return: The optional result of the visit.
        """

    @abstractmethod
    def visit_field_range(self, qt: FieldRangeQuery) -> Optional[T]:
        """
        Visit a FieldRangeQuery query term and compute an optional result.
        :param qt: The FieldRangeQuery query term to be visited.
        :return: The optional result of the visit.
        """

    @abstractmethod
    def visit_field_wildcard(self, qt: FieldWildcardQuery) -> Optional[T]:
        """
        Visit a FieldRangeQuery query term and compute an optional result.
        :param qt: The FieldRangeQuery query term to be visited.
        :return: The optional result of the visit.
        """


# noinspection PyPep8Naming
class QueryBuilder:

    @classmethod
    def value(cls, value: Value, name: str = None):
        return FieldValueQuery(name, value)

    @classmethod
    def range(cls, from_value: Value, to_value: Value, is_exclusive=False, name: str = None):
        return FieldRangeQuery(name, from_value, to_value, is_exclusive=is_exclusive)

    @classmethod
    def wildcard(cls, value: str, name: str = None):
        return FieldWildcardQuery(name, value)

    @classmethod
    def include(cls, t: FieldQuery):
        return UnaryOpQuery('+', t)

    @classmethod
    def exclude(cls, t: FieldQuery):
        return UnaryOpQuery('-', t)

    @classmethod
    def phrase(cls, *terms: Query):
        return PhraseQuery(terms)

    @classmethod
    def NOT(cls, t: Query):
        return UnaryOpQuery('NOT', t)

    @classmethod
    def AND(cls, t1: Query, t2: Query):
        return BinaryOpQuery('AND', t1, t2)

    @classmethod
    def OR(cls, t1: Query, t2: Query):
        return BinaryOpQuery('OR', t1, t2)