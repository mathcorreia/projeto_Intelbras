"""
JWT Middleware — Fase 7.

Extrai tenant_id do JWT emitido pelo Java backendPerm.
Ativado automaticamente quando JWT_SECRET está configurado.
Em dev sem a env var: retorna tenant_id=1 (modo single-tenant).

Usage (FastAPI dependency):
    @router.get("/cameras")
    def list_cameras(tenant_id: int = Depends(get_current_tenant_id), db = Depends(get_db)):
        return crud.get_cameras(db, tenant_id=tenant_id)
"""

import os
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_JWT_SECRET = os.getenv("JWT_SECRET") or ""
_DEV_MODE = not _JWT_SECRET

_bearer = HTTPBearer(auto_error=False)


def get_current_tenant_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> int:
    """
    FastAPI dependency.
    - JWT_SECRET ausente (dev): sempre retorna 1.
    - JWT_SECRET presente (prod): valida Bearer token, extrai tenant_id.
    """
    if _DEV_MODE:
        return 1

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação necessário",
        )

    try:
        import jwt as pyjwt
        payload = pyjwt.decode(
            credentials.credentials,
            _JWT_SECRET,
            algorithms=["HS256"],
        )
        tenant_id = payload.get("tenant_id")
        if tenant_id is None:
            raise HTTPException(status_code=403, detail="Token sem tenant_id")
        return int(tenant_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )
