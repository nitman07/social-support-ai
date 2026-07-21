import os
from typing import Any

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")


def _headers() -> dict:
    token = st.session_state.get("token")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def login(username: str, password: str) -> dict | None:
    try:
        resp = httpx.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


def get_me() -> dict | None:
    try:
        resp = httpx.get(f"{API_BASE_URL}/api/v1/auth/me", headers=_headers(), timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


def list_applications(status: str | None = None, page: int = 1, page_size: int = 20) -> dict:
    params: dict[str, Any] = {"page": page, "page_size": page_size}
    if status:
        params["status"] = status
    resp = httpx.get(
        f"{API_BASE_URL}/api/v1/applications",
        headers=_headers(),
        params=params,
        timeout=10,
    )
    return resp.json() if resp.status_code == 200 else {"items": [], "total": 0, "page": page, "page_size": page_size}


def get_application(app_id: str) -> dict | None:
    resp = httpx.get(
        f"{API_BASE_URL}/api/v1/applications/{app_id}",
        headers=_headers(),
        timeout=10,
    )
    return resp.json() if resp.status_code == 200 else None


def process_application(app_id: str) -> dict | None:
    resp = httpx.post(
        f"{API_BASE_URL}/api/v1/applications/{app_id}/process",
        headers=_headers(),
        timeout=10,
    )
    return resp.json() if resp.status_code in (200, 202) else None


def get_status(app_id: str) -> dict | None:
    resp = httpx.get(
        f"{API_BASE_URL}/api/v1/applications/{app_id}/status",
        headers=_headers(),
        timeout=10,
    )
    return resp.json() if resp.status_code == 200 else None


def get_flags(app_id: str) -> list:
    resp = httpx.get(
        f"{API_BASE_URL}/api/v1/applications/{app_id}/flags",
        headers=_headers(),
        timeout=10,
    )
    return resp.json() if resp.status_code == 200 else []


def resolve_flag(app_id: str, flag_id: str, action: str, note: str | None = None) -> bool:
    resp = httpx.post(
        f"{API_BASE_URL}/api/v1/applications/{app_id}/resolve-flag/{flag_id}",
        headers=_headers(),
        json={"action": action, "note": note},
        timeout=10,
    )
    return resp.status_code == 200


def signoff(app_id: str, decision: str, rationale: str | None = None) -> bool:
    resp = httpx.post(
        f"{API_BASE_URL}/api/v1/applications/{app_id}/signoff",
        headers=_headers(),
        json={"decision": decision, "rationale": rationale},
        timeout=10,
    )
    return resp.status_code == 200


def resume_workflow(app_id: str) -> dict | None:
    resp = httpx.post(
        f"{API_BASE_URL}/api/v1/applications/{app_id}/resume",
        headers=_headers(),
        timeout=10,
    )
    return resp.json() if resp.status_code == 200 else None
