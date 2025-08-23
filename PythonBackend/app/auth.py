from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer
from supabase import create_client
import jwt

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
security = HTTPBearer()

def get_current_user(token: str = Depends(security)):
    try:
        # Verify the JWT token with Supabase
        user = supabase.auth.get_user(token.credentials)
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/protected")
def protected_route(user = Depends(get_current_user)):
    return {"user_id": user.user.id}