import hashlib
import json


def operation_fingerprint(input_fingerprint, operation, config, seed, engine_version="1.0.0"):
    payload = {
        "input": input_fingerprint,
        "operation": operation,
        "config": config,
        "seed": seed,
        "engine_version": engine_version,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    ).hexdigest()
