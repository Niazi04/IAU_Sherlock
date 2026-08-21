class APIKeyInvalid(Exception):
    """Invalid API Key for current service"""
class RateLimit(Exception):
    """You have hit our rate limit"""
class ProviderAPIErr(Exception):
    """Provider gateway err"""