"""API key management endpoints"""
from fastapi import APIRouter, HTTPException
import httpx
import sqlite3
from datetime import datetime
from models import APIKeyRequest
from encryption import cipher
from database import mask_key

router = APIRouter(tags=["api-keys"])


@router.post("/verify-key")
async def verify_api_key(request: APIKeyRequest):
    """Verify OpenAI API key by making a test API call"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {request.key}"},
                timeout=10.0
            )

            if response.status_code == 200:
                return {"valid": True, "message": "API key is valid"}
            else:
                return {"valid": False, "message": "Invalid API key"}
    except Exception as e:
        return {"valid": False, "message": f"Verification failed: {str(e)}"}


@router.post("/save-key")
async def save_api_key(request: APIKeyRequest):
    """Encrypt and save API key"""
    try:
        # Verify key first
        verification = await verify_api_key(request)
        if not verification["valid"]:
            raise HTTPException(status_code=400, detail="Invalid API key")

        # Encrypt the key
        encrypted_key = cipher.encrypt(request.key.encode())

        # Save to database
        conn = sqlite3.connect('data/settings.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO api_keys (service, encrypted_key, partial_key, last_verified)
            VALUES (?, ?, ?, ?)
        ''', ('openai', encrypted_key.decode(), mask_key(request.key), datetime.now()))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "partial_key": mask_key(request.key)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-key")
async def get_api_key():
    """Get decrypted API key for internal service use"""
    conn = sqlite3.connect('data/settings.db')
    cursor = conn.cursor()
    result = cursor.execute(
        "SELECT encrypted_key FROM api_keys WHERE service = 'openai'"
    ).fetchone()
    conn.close()

    if result:
        decrypted = cipher.decrypt(result[0].encode())
        return {"key": decrypted.decode()}

    raise HTTPException(status_code=404, detail="No API key found")


@router.get("/key-status")
async def get_key_status():
    """Get API key status without revealing the key"""
    conn = sqlite3.connect('data/settings.db')
    cursor = conn.cursor()
    result = cursor.execute(
        "SELECT partial_key, last_verified FROM api_keys WHERE service = 'openai'"
    ).fetchone()
    conn.close()

    if result:
        return {
            "exists": True,
            "partial_key": result[0],
            "last_verified": result[1]
        }

    return {"exists": False}
