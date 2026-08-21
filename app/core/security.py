import hmac


def verify_api_key(candidate: str, valid_key: str) -> bool:
    return hmac.compare_digest(
        candidate.encode("utf-8"),
        valid_key.encode("utf-8"),
    )