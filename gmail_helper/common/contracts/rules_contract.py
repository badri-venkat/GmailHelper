from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class MatchType(str, Enum):
    all = "all"
    any = "any"


class FieldName(str, Enum):
    From_ = "From"
    To = "To"
    Subject = "Subject"
    Message = "Message"
    DateReceived = "DateReceived"


class StringPredicate(str, Enum):
    contains = "contains"
    does_not_contain = "does_not_contain"
    equals = "equals"
    does_not_equal = "does_not_equal"


class DatePredicate(str, Enum):
    less_than_days = "less_than_days"
    greater_than_days = "greater_than_days"
    less_than_months = "less_than_months"
    greater_than_months = "greater_than_months"


Predicate = Union[StringPredicate, DatePredicate]


class Condition(BaseModel):
    field: FieldName
    predicate: Predicate
    value: Union[str, int, float]


class ActionType(str, Enum):
    mark_as_read = "mark_as_read"
    mark_as_unread = "mark_as_unread"
    move_message = "move_message"


class Action(BaseModel):
    type: ActionType
    mailbox: Optional[str] = None  # required when type == move_message


class Rule(BaseModel):
    description: str = Field(default="Rule")
    match: MatchType = Field(default=MatchType.all)
    conditions: List[Condition]
    actions: List[Action] = Field(default_factory=list)
