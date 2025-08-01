from dotenv import load_dotenv

load_dotenv()
import hashlib
from datetime import datetime, UTC
from fastapi import HTTPException, Header
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Any
from db import get_db


# On key creation
def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


class AccessKeys:

    def __init__(self) -> None:
        self.keys: dict[str, dict[str, Any]] = {}

    def setup_keystore(self, records: list[dict[str, Any]]) -> None:
        self.keys = {
            record["keyhash"]: {k: v for k, v in record.items() if k != "keyhash"}
            for record in records
        }

    def valid_key(self, key) -> bool:
        if not self.keys:
            return False
        incoming_keyhash = hash_api_key(key)
        stored_key = self.keys.get(incoming_keyhash, None)
        if not stored_key or stored_key["revoked"]:
            return False
        expiry = stored_key["expires"]
        return expiry is None or expiry > datetime.now(UTC)


async def access_gate(x_access_key: str = Header(None)):
    if not x_access_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    if not access_keys.valid_key(x_access_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Update last_used
    stored_key = access_keys.keys.get(hash_api_key(x_access_key))
    if stored_key:
        db: Session = next(get_db())
        try:
            sql = """
                UPDATE data_api_access_keys
                SET last_used = :now
                WHERE id = :key_id
            """
            db.execute(
                text(sql), {"now": datetime.now(UTC), "key_id": stored_key["id"]}
            )
            db.commit()
        finally:
            db.close()


access_keys = AccessKeys()
