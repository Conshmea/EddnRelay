import re
import logging
from typing import Any, Dict, Sequence, Union, List

logger = logging.getLogger('EddnRelay')

class FilterCondition:
    """Base class for all filter conditions."""
    def matches(self, data: Dict) -> bool:
        """
        Check if the condition matches the given data.
        
        Args:
            data: The data to check against the condition
            
        Returns:
            bool: True if the condition matches, False otherwise
        """
        raise NotImplementedError

ConditionType = Union[
    'ExistsCondition',
    'ExactCondition',
    'RegexCondition',
    'AllCondition',
    'AnyCondition'
]

class ExistsCondition(FilterCondition):
    """
    A condition that matches when a value at a specified path exists in the data.
    
    Attributes:
        path: Sequence of keys to traverse in the data
    """
    def __init__(self, path: Sequence[str]):
        """
        Initialize an existence condition.
        
        Args:
            path: Sequence of keys to traverse in the data
        """
        self.path = path
        logger.debug("Adding exists filter for path: %s", '.'.join(path))
        
    def matches(self, data: Dict) -> bool:
        """Check if the """
        return self.check_value(data, list(self.path))

    def check_value(self, data: Dict, path: List[str]) -> bool:
        """
        Check if the value at the specified path matches the target value.
        
        Args:
            data: The data to check against
        """
        current = data
        remaining_path = list(path)
        for key in path:
            if isinstance(current, list):
                return any(self.check_value(item, remaining_path.copy()) for item in current)
            if not isinstance(current, dict) or key not in current:
                logger.debug("ExistsCondition: Path %s not found in data", '.'.join(self.path))
                return False
            current = current[key]
            remaining_path = remaining_path[1:]
        result = current is not None
        logger.debug("ExistsCondition: Path %s match result: %s", '.'.join(self.path), result)
        return result

class ExactCondition(FilterCondition):
    """
    A condition that matches when a value at a specified path exactly equals the target value.
    
    Attributes:
        path: Sequence of keys to traverse in the data
        value: The value to match against
    """

    def __init__(self, path: Sequence[str], value: Any):
        """
        Initialize an exact match condition.
        
        Args:
            path: Sequence of keys to traverse in the data
            value: The value to match against
        """
        self.path = path
        self.value = value
        logger.debug("Adding exact filter for path: %s with value: %s", '.'.join(path), value)

    def matches(self, data: Dict) -> bool:
        """Check if the value at the specified path exactly matches the target value."""
        return self.check_value(data, list(self.path))

    def check_value(self, data: Dict, path: List[str]) -> bool:
        """
        Check if the value at the specified path matches the target value.
        
        Args:
            data: The data to check against
        """
        current = data
        remaining_path = list(path)
        for key in path:
            if isinstance(current, list):
                return any(self.check_value(item, remaining_path.copy()) for item in current)
            if not isinstance(current, dict) or key not in current:
                logger.debug("ExactCondition: Path %s not found in data", '.'.join(self.path))
                return False
            current = current[key]
            remaining_path = remaining_path[1:]
        result = current == self.value
        logger.debug("ExactCondition: Path %s match result: %s", '.'.join(self.path), result)
        return result

class RegexCondition(FilterCondition):
    """
    A condition that matches when a value at a specified path matches a regular expression.
    
    Attributes:
        path: Sequence of keys to traverse in the data
        regex: Compiled regular expression pattern
    """

    def __init__(self, path: Sequence[str], pattern: str):
        """
        Initialize a regex match condition.
        
        Args:
            path: Sequence of keys to traverse in the data
            pattern: Regular expression pattern to match against
            
        Raises:
            re.error: If the pattern is invalid
        """
        self.path = path
        try:
            self.regex = re.compile(pattern)
            logger.debug("RegexCondition: Created filter for path %s with pattern %s",
                        '.'.join(path), pattern)
        except re.error as e:
            logger.error("RegexCondition: Invalid regex pattern '%s': %s", pattern, str(e))
            raise

    def matches(self, data: Dict) -> bool:
        """Check if the value at the specified path matches the regex pattern."""
        return self.check_value(data, list(self.path))

    def check_value(self, data: Dict, path: List[str]) -> bool:
        """
        Check if the value at the specified path matches the target value.
        
        Args:
            data: The data to check against
        """
        current = data
        remaining_path = list(path)
        for key in path:
            if isinstance(current, list):
                return any(self.check_value(item, remaining_path.copy()) for item in current)
            if not isinstance(current, dict) or key not in current:
                logger.debug("RegexCondition: Path %s not found in data", '.'.join(self.path))
                return False
            current = current[key]
            remaining_path = remaining_path[1:]
        result = bool(self.regex.match(str(current)))
        logger.debug("RegexCondition: Path %s match result: %s", '.'.join(self.path), result)
        return result

class AllCondition(FilterCondition):
    """
    A condition that matches when all of its sub-conditions match (logical AND).
    
    Attributes:
        conditions: List of conditions that must all match
    """

    def __init__(self, conditions: Sequence[ConditionType]):
        """
        Initialize an AND condition.
        
        Args:
            conditions: Sequence of conditions that must all match
        """
        self.conditions: List[ConditionType] = list(conditions)

    def matches(self, data: Dict) -> bool:
        """Check if all sub-conditions match the data."""
        return all(condition.matches(data) for condition in self.conditions)

class AnyCondition(FilterCondition):
    """
    A condition that matches when any of its sub-conditions match (logical OR).
    
    Attributes:
        conditions: List of conditions where at least one must match
    """

    def __init__(self, conditions: Sequence[ConditionType]):
        """
        Initialize an OR condition.
        
        Args:
            conditions: Sequence of conditions where at least one must match
        """
        self.conditions: List[ConditionType] = list(conditions)

    def matches(self, data: Dict) -> bool:
        """Check if any sub-condition matches the data."""
        return any(condition.matches(data) for condition in self.conditions)

class Filter:
    """
    A filter that can contain multiple conditions to match against EDDN messages.
    
    Attributes:
        root_condition: The top-level condition for this filter
    """

    def __init__(self):
        """Initialize a filter with an empty AllCondition."""
        logger.debug("Creating new Filter instance")
        self.root_condition: FilterCondition = AllCondition([])

    def add_exact_filter(self, path: Sequence[str], value: Any) -> None:
        """
        Add an exact match filter condition.
        
        Args:
            path: Sequence of keys to traverse in the data
            value: The value to match against
        """
        if isinstance(self.root_condition, AllCondition):
            self.root_condition.conditions.append(ExactCondition(path, value))

    def add_regex_filter(self, path: Sequence[str], pattern: str) -> None:
        """
        Add a regex match filter condition.
        
        Args:
            path: Sequence of keys to traverse in the data
            pattern: Regular expression pattern to match against
        """
        if isinstance(self.root_condition, AllCondition):
            self.root_condition.conditions.append(RegexCondition(path, pattern))

    def set_condition(self, condition: FilterCondition) -> None:
        """
        Set the root condition for this filter.
        
        Args:
            condition: The new root condition
        """
        logger.debug("Setting new root condition of type: %s", condition.__class__.__name__)
        self.root_condition = condition

    def matches(self, data: Dict) -> bool:
        """
        Check if the data matches this filter's conditions.
        
        Args:
            data: The data to check against the filter
            
        Returns:
            bool: True if the filter matches, False otherwise
        """
        result = self.root_condition.matches(data)
        logger.debug("Filter match result: %s", result)
        return result
