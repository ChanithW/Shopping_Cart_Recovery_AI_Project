"""
Cart Abandonment Detection System
Detects abandoned carts and sends personalized recovery emails with AI-powered recommendations.
"""

from .cart_abandonment_detector import (
    CartAbandonmentDetector,
    EmailService,
    RecommendationEngine,
    start_abandonment_monitor
)

__all__ = [
    'CartAbandonmentDetector',
    'EmailService',
    'RecommendationEngine',
    'start_abandonment_monitor'
]

__version__ = '1.0.0'
