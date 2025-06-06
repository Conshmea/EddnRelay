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
        
    def to_mongo_query(self) -> dict:
        """
        Convert the condition to a MongoDB query.
        
        Returns:
            dict: A MongoDB query that represents this condition
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

    def to_mongo_query(self) -> dict:
        """Convert to MongoDB exists query."""
        path = '.'.join(self.path)
        return {path: {'$exists': True}}

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

    def to_mongo_query(self) -> dict:
        """Convert to MongoDB exact match query."""
        path = '.'.join(self.path)
        return {path: self.value}

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

    def to_mongo_query(self) -> dict:
        """Convert to MongoDB regex query."""
        path = '.'.join(self.path)
        return {path: {'$regex': self.regex.pattern}}

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

    def to_mongo_query(self) -> dict:
        """Convert to MongoDB AND query."""
        if not self.conditions:
            return {}
        return {'$and': [c.to_mongo_query() for c in self.conditions]}

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

    def to_mongo_query(self) -> dict:
        """Convert to MongoDB OR query."""
        if not self.conditions:
            return {}
        return {'$or': [c.to_mongo_query() for c in self.conditions]}

class Filter:
    """
    A filter that can contain multiple conditions to match against EDDN messages.
    
    Attributes:
        root_condition: The top-level condition for this filter
        pattern: A regex pattern that represents all filter conditions combined
    """

    def __init__(self):
        """Initialize a filter with an empty AllCondition."""
        logger.debug("Creating new Filter instance")
        self.root_condition: FilterCondition = AllCondition([])
        self.pattern: str = ".*"  # Default pattern matches everything
    
    def _build_pattern(self, condition: FilterCondition) -> str:
        """
        Build a regex pattern from a filter condition.
        
        Args:
            condition: The condition to build a pattern from
            
        Returns:
            str: A regex pattern representing the condition
        """
        if isinstance(condition, ExistsCondition):
            path = '.'.join(condition.path)
            return f'(?=.*"{path}")'
        elif isinstance(condition, ExactCondition):
            path = '.'.join(condition.path)
            value = re.escape(str(condition.value))
            return f'(?=.*"{path}"\\s*:\\s*"{value}")'
        elif isinstance(condition, RegexCondition):
            path = '.'.join(condition.path)
            return f'(?=.*"{path}"\\s*:\\s*{condition.regex.pattern})'
        elif isinstance(condition, AllCondition):
            patterns = [self._build_pattern(c) for c in condition.conditions]
            return ''.join(patterns)
        elif isinstance(condition, AnyCondition):
            patterns = [self._build_pattern(c) for c in condition.conditions]
            return '|'.join(f'({p})' for p in patterns)
        return ".*"

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
    
    def set_filter_from_json(self, condition_data: dict) -> None:
        """
        Set the filter conditions from JSON data.
        
        Args:
            condition_data: Dictionary containing filter configuration
            
        Raises:
            ValueError: If condition type is unknown
            KeyError: If required fields are missing
        """
        try:
            self.root_condition = self._parse_condition_from_json(condition_data)
            self.pattern = self._build_pattern(self.root_condition)
        except (ValueError, KeyError) as e:
            logger.error("Failed to set filters from JSON: %s", e)
            raise
    
    def _parse_condition_from_json(self, condition_data: dict) -> ExistsCondition  | RegexCondition | ExactCondition | AllCondition | AnyCondition:
        """
        Parse a filter condition from client data.
        
        Args:
            condition_data: Dictionary containing condition configuration
            
        Returns:
            FilterCondition: The parsed filter condition object
            
        Raises:
            ValueError: If condition type is unknown
            KeyError: If required fields are missing
        """
        try:
            if condition_data['type'] == 'exists':
                return ExistsCondition(condition_data['path'].split('.'))
            elif condition_data['type'] == 'exact':
                return ExactCondition(condition_data['path'].split('.'), condition_data['value'])
            elif condition_data['type'] == 'regex':
                return RegexCondition(condition_data['path'].split('.'), condition_data['pattern'])
            elif condition_data['type'] == 'all':
                conditions = [self._parse_condition_from_json(c) for c in condition_data['conditions']]
                return AllCondition(conditions)
            elif condition_data['type'] == 'any':
                conditions = [self._parse_condition_from_json(c) for c in condition_data['conditions']]
                return AnyCondition(conditions)
            raise ValueError(f"Unknown condition type: {condition_data['type']}")
        except KeyError as e:
            logger.error("Missing required field in condition data: %s", e)
            raise
        except ValueError as e:
            logger.error("Invalid condition data: %s", e)
            raise

    def to_mongo_query(self) -> dict:
        """
        Convert the filter to a MongoDB query.
        
        Returns:
            dict: A MongoDB query that represents all filter conditions
        """
        return self.root_condition.to_mongo_query()
