from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.db.supabase import get_supabase_client

security = HTTPBearer()


class User(BaseModel):
    id: str
    email: str | None = None
    is_admin: bool = False


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Validate the Supabase access token and load the authenticated user profile."""
    token = credentials.credentials

    try:
        # Supabase validates the JWT server-side before returning the user.  This
        # avoids trusting unverified claims from a locally decoded token.
        auth_response = get_supabase_client().auth.get_user(token)
        auth_user = auth_response.user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token"
        ) from None

    if not auth_user or not auth_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token"
        )

    # Query user_profiles for the application-level admin role. A database
    # failure is deliberately not reported as an authentication failure.
    supabase = get_supabase_client()
    profile_result = supabase.table("user_profiles").select("is_admin").eq(
        "user_id", auth_user.id
    ).maybe_single().execute()

    is_admin = False
    if profile_result and profile_result.data:
        is_admin = profile_result.data.get("is_admin", False)

    return User(id=auth_user.id, email=auth_user.email, is_admin=is_admin)


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require the current user to be an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
