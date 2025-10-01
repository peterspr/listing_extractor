"""
Calculation helpers for commercial real estate metrics
"""
import logging
import re
from typing import Optional, Union

logger = logging.getLogger(__name__)


class RentCalculator:
    """Helper class for commercial real estate rent calculations"""
    
    @staticmethod
    def parse_square_footage(sf_text: str) -> Optional[float]:
        """
        Parse square footage from text
        
        Args:
            sf_text: Text containing square footage (e.g., "11,500 SF", "11500", "11.5K SF")
            
        Returns:
            Square footage as float or None if parsing fails
        """
        if not sf_text or sf_text.upper() in ['N/A', 'NA', '']:
            return None
        
        try:
            # Remove common suffixes and formatting
            cleaned = re.sub(r'[,\s]', '', str(sf_text).upper())
            cleaned = re.sub(r'SF|SQ\.?FT\.?|SQFT', '', cleaned)
            
            # Handle K suffix (thousands)
            if 'K' in cleaned:
                number = float(re.sub(r'[^0-9.]', '', cleaned))
                return number * 1000
            
            # Extract numeric value
            match = re.search(r'(\d+(?:\.\d+)?)', cleaned)
            if match:
                return float(match.group(1))
            
            return None
            
        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not parse square footage '{sf_text}': {str(e)}")
            return None
    
    @staticmethod
    def parse_rate(rate_text: str) -> Optional[float]:
        """
        Parse lease rate from text
        
        Args:
            rate_text: Text containing rate (e.g., "$0.80/SF", "0.80", "$9.60/SF/YR")
            
        Returns:
            Rate as float or None if parsing fails
        """
        if not rate_text or rate_text.upper() in ['N/A', 'NA', '']:
            return None
        
        try:
            # Remove currency symbols and common formatting
            cleaned = re.sub(r'[$,\s]', '', str(rate_text).upper())
            cleaned = re.sub(r'/SF|/SQFT|/YR|/YEAR|/MO|/MONTH', '', cleaned)
            
            # Extract numeric value
            match = re.search(r'(\d+(?:\.\d+)?)', cleaned)
            if match:
                return float(match.group(1))
            
            return None
            
        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not parse rate '{rate_text}': {str(e)}")
            return None
    
    @staticmethod
    def calculate_monthly_base_rent(shell_sf: Optional[float], shell_rate: Optional[float], 
                                   office_sf: Optional[float] = None, office_rate: Optional[float] = None) -> Optional[float]:
        """
        Calculate monthly base rent
        
        Args:
            shell_sf: Shell/warehouse square footage
            shell_rate: Shell lease rate ($/SF/month)
            office_sf: Office square footage (optional)
            office_rate: Office lease rate ($/SF/month, optional)
            
        Returns:
            Monthly base rent or None if calculation not possible
        """
        try:
            total_rent = 0.0
            
            # Shell/warehouse rent
            if shell_sf and shell_rate:
                total_rent += shell_sf * shell_rate
            
            # Office rent
            if office_sf and office_rate:
                total_rent += office_sf * office_rate
            
            return total_rent if total_rent > 0 else None
            
        except (TypeError, ValueError) as e:
            logger.warning(f"Could not calculate monthly base rent: {str(e)}")
            return None
    
    @staticmethod
    def calculate_blended_rate(total_rent: Optional[float], total_sf: Optional[float]) -> Optional[float]:
        """
        Calculate blended rate per square foot
        
        Args:
            total_rent: Total rent amount
            total_sf: Total square footage
            
        Returns:
            Blended rate per SF or None if calculation not possible
        """
        try:
            if total_rent and total_sf and total_sf > 0:
                return total_rent / total_sf
            return None
            
        except (TypeError, ValueError, ZeroDivisionError) as e:
            logger.warning(f"Could not calculate blended rate: {str(e)}")
            return None
    
    @staticmethod
    def monthly_to_annual_rate(monthly_rate: Optional[float]) -> Optional[float]:
        """Convert monthly rate to annual rate"""
        try:
            if monthly_rate:
                return monthly_rate * 12
            return None
        except (TypeError, ValueError) as e:
            logger.warning(f"Could not convert monthly to annual rate: {str(e)}")
            return None
    
    @staticmethod
    def annual_to_monthly_rate(annual_rate: Optional[float]) -> Optional[float]:
        """Convert annual rate to monthly rate"""
        try:
            if annual_rate:
                return annual_rate / 12
            return None
        except (TypeError, ValueError) as e:
            logger.warning(f"Could not convert annual to monthly rate: {str(e)}")
            return None
    
    @staticmethod
    def add_operating_expenses(base_rent: Optional[float], opex_rate: Optional[float], 
                              total_sf: Optional[float]) -> Optional[float]:
        """
        Add operating expenses to base rent
        
        Args:
            base_rent: Base monthly rent
            opex_rate: Operating expense rate ($/SF/month)
            total_sf: Total square footage
            
        Returns:
            Gross rent including operating expenses
        """
        try:
            if not base_rent:
                return None
            
            gross_rent = base_rent
            
            if opex_rate and total_sf:
                gross_rent += opex_rate * total_sf
            
            return gross_rent
            
        except (TypeError, ValueError) as e:
            logger.warning(f"Could not calculate gross rent: {str(e)}")
            return None
    
    @staticmethod
    def validate_numeric_field(value: Union[str, float, None], field_name: str, 
                              min_value: float = 0, max_value: float = float('inf')) -> bool:
        """
        Validate numeric field values for reasonableness
        
        Args:
            value: Value to validate
            field_name: Name of field for logging
            min_value: Minimum acceptable value
            max_value: Maximum acceptable value
            
        Returns:
            True if value is valid, False otherwise
        """
        try:
            if value is None or value == "N/A":
                return True  # Missing values are acceptable
            
            numeric_value = float(value) if isinstance(value, str) else value
            
            if not (min_value <= numeric_value <= max_value):
                logger.warning(f"Suspicious {field_name} value: {numeric_value} (expected {min_value}-{max_value})")
                return False
            
            return True
            
        except (ValueError, TypeError):
            logger.warning(f"Invalid {field_name} value: {value}")
            return False
    
    @staticmethod
    def format_currency(amount: Optional[float], decimals: int = 2) -> str:
        """Format amount as currency string"""
        try:
            if amount is None:
                return "N/A"
            return f"{amount:.{decimals}f}"
        except (TypeError, ValueError):
            return "N/A"
    
    @staticmethod
    def format_square_footage(sf: Optional[float]) -> str:
        """Format square footage as string"""
        try:
            if sf is None:
                return "N/A"
            return f"{int(sf):,}" if sf == int(sf) else f"{sf:,.1f}"
        except (TypeError, ValueError):
            return "N/A"


# Validation constants for commercial real estate
class ValidationLimits:
    """Constants for validating commercial real estate data"""
    
    # Square footage limits
    MIN_SF = 100
    MAX_SF = 10_000_000  # 10M SF for very large facilities
    
    # Rate limits ($/SF/month)
    MIN_MONTHLY_RATE = 0.01
    MAX_MONTHLY_RATE = 20.0  # $20/SF/month is very high
    
    # Annual rate limits ($/SF/year)
    MIN_ANNUAL_RATE = 0.12  # $0.01/month * 12
    MAX_ANNUAL_RATE = 240.0  # $20/month * 12
    
    # Monthly rent limits
    MIN_MONTHLY_RENT = 100
    MAX_MONTHLY_RENT = 10_000_000  # $10M/month for very large facilities
    
    # Operating expense limits ($/SF/month)
    MIN_OPEX = 0.01
    MAX_OPEX = 5.0  # $5/SF/month for OpEx
    
    # Clear height limits (feet)
    MIN_CLEAR_HEIGHT = 8
    MAX_CLEAR_HEIGHT = 100


def validate_extraction_data(data: dict) -> dict:
    """
    Validate extracted data and flag suspicious values
    
    Args:
        data: Dictionary of extracted data
        
    Returns:
        Dictionary with validation results
    """
    warnings = []
    calc = RentCalculator()
    
    # Validate square footage
    shell_sf = calc.parse_square_footage(data.get('Shell SF'))
    if shell_sf and not calc.validate_numeric_field(shell_sf, 'Shell SF', 
                                                   ValidationLimits.MIN_SF, ValidationLimits.MAX_SF):
        warnings.append(f"Suspicious Shell SF: {shell_sf}")
    
    office_sf = calc.parse_square_footage(data.get('Office SF'))
    if office_sf and not calc.validate_numeric_field(office_sf, 'Office SF', 
                                                    ValidationLimits.MIN_SF, ValidationLimits.MAX_SF):
        warnings.append(f"Suspicious Office SF: {office_sf}")
    
    # Validate rates
    shell_rate = calc.parse_rate(data.get('Shell Rate'))
    if shell_rate and not calc.validate_numeric_field(shell_rate, 'Shell Rate', 
                                                     ValidationLimits.MIN_MONTHLY_RATE, ValidationLimits.MAX_MONTHLY_RATE):
        warnings.append(f"Suspicious Shell Rate: {shell_rate}")
    
    office_rate = calc.parse_rate(data.get('Office Rate'))
    if office_rate and not calc.validate_numeric_field(office_rate, 'Office Rate', 
                                                      ValidationLimits.MIN_MONTHLY_RATE, ValidationLimits.MAX_MONTHLY_RATE):
        warnings.append(f"Suspicious Office Rate: {office_rate}")
    
    # Validate monthly rent
    monthly_rent = calc.parse_rate(data.get('Monthly Base Rent'))
    if monthly_rent and not calc.validate_numeric_field(monthly_rent, 'Monthly Base Rent', 
                                                       ValidationLimits.MIN_MONTHLY_RENT, ValidationLimits.MAX_MONTHLY_RENT):
        warnings.append(f"Suspicious Monthly Base Rent: {monthly_rent}")
    
    return {
        'valid': len(warnings) == 0,
        'warnings': warnings,
        'parsed_values': {
            'shell_sf': shell_sf,
            'office_sf': office_sf,
            'shell_rate': shell_rate,
            'office_rate': office_rate,
            'monthly_rent': monthly_rent
        }
    }