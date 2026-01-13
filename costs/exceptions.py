"""Custom exceptions for the cost simulation system."""


class CostSimulationError(Exception):
    """Base exception for cost simulation errors."""

    pass


class ConfigurationError(CostSimulationError):
    """Raised when configuration is invalid or missing."""

    pass


class InvalidLoadError(CostSimulationError):
    """Raised when load data is invalid."""

    pass


class ResourceCalculationError(CostSimulationError):
    """Raised when resource calculation fails."""

    pass


class CostCalculationError(CostSimulationError):
    """Raised when cost calculation fails."""

    pass


class InstanceNotFoundError(CostSimulationError):
    """Raised when requested instance type is not available."""

    pass


class PricingDataError(CostSimulationError):
    """Raised when pricing data is missing or invalid."""

    pass


class JMeterParseError(CostSimulationError):
    """Raised when JMeter result parsing fails."""

    pass


class FrameworkConfigError(CostSimulationError):
    """Raised when framework configuration is invalid."""

    pass
