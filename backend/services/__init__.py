# NEW_FILE_CODE
from .weather_service import get_weather_for_date, update_schedules_weather_for_user
from .nlp_parser import parse_natural_language
from .conflict_detector import detect_schedule_conflicts
from .recommendation_engine import generate_schedule_recommendations

__all__ = [
    'get_weather_for_date',
    'update_schedules_weather_for_user',
    'parse_natural_language',
    'detect_schedule_conflicts',
    'generate_schedule_recommendations'
]