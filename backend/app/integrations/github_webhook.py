import hmac
from hashlib import sha256


def verify_github_webhook_signature(
    *,
    payload: bytes,
    signature: str | None,
    secret: str,
) -> bool:
    """Verify GitHub's raw-body HMAC without parsing untrusted JSON first."""
    if signature is None or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload,
        sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
