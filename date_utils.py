import dateutil.parser
from datetime import datetime, timedelta

def parse_date(date_string):
    try:
        # Try parsing with dateutil
        parsed_date = dateutil.parser.parse(date_string, fuzzy=True)
        
        # If year is not provided, assume it's the current year or next year
        if parsed_date.year == 1900:
            current_year = datetime.now().year
            parsed_date = parsed_date.replace(year=current_year)
            if parsed_date < datetime.now():
                parsed_date = parsed_date.replace(year=current_year + 1)
        
        return parsed_date.strftime("%d-%m-%Y")
    except ValueError:
        return None

def validate_date_range(check_in, check_out):
    try:
        check_in_date = datetime.strptime(check_in, "%d-%m-%Y")
        check_out_date = datetime.strptime(check_out, "%d-%m-%Y")
        
        if check_in_date >= check_out_date:
            return False
        
        if check_in_date < datetime.now().date():
            return False
        
        if (check_out_date - check_in_date).days > 30:
            return False
        
        return True
    except ValueError:
        return False

def get_date_suggestions(date_string):
    try:
        parsed_date = dateutil.parser.parse(date_string, fuzzy=True)
        suggestions = [
            parsed_date.strftime("%d-%m-%Y"),
            parsed_date.strftime("%Y-%m-%d"),
            parsed_date.strftime("%B %d, %Y"),
            parsed_date.strftime("%d %B %Y"),
        ]
        return suggestions
    except ValueError:
        return []
