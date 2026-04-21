from typing import Any, TypeGuard, cast


def is_json_object(value: object) -> TypeGuard[dict[str, Any]]:
    if not isinstance(value, dict):
        return False
    typedValue = cast(dict[object, Any], value)
    return all(isinstance(key, str) for key in typedValue)
