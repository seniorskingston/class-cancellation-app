"""Routes for the new function.

These routes are added only when FEATURE_NEW_FUNCTION=true.
Existing pages and API addresses are unchanged when the flag is off.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/new-function", tags=["new-function"])


@router.get("")
def new_function_status():
    return {
        "module": "new_function",
        "enabled": True,
        "message": "The new function is turned on. Existing pages are unchanged.",
    }
