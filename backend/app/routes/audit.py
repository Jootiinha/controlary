"""
Audit Log Routes

Endpoints for viewing and exporting audit logs.
Restricted to authenticated users viewing their own activity or admins viewing all logs.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.utils.decorators import get_current_user
from app.services.audit_service import AuditService
from app.models.audit_log import AuditLog

router = APIRouter()


class AuditLogResponse(BaseModel):
    """Audit log response model."""
    id: int
    user_id: Optional[str]
    operation: str
    resource_type: str
    resource_id: Optional[str]
    client_ip: Optional[str]
    endpoint: str
    status: str
    status_code: Optional[int]
    created_at: Optional[str]

    class Config:
        from_attributes = True


@router.get("/audit-logs/my-activity", response_model=List[AuditLogResponse])
async def get_my_activity(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get authenticated user's own activity logs.

    Allows users to see their own login history, data modifications, etc.
    """
    logs = AuditService.get_user_activity(
        db,
        user_id=user_id,
        days=days,
        limit=limit,
    )
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "operation": log.operation,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "client_ip": log.client_ip,
            "endpoint": log.endpoint,
            "status": log.status,
            "status_code": log.status_code,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/audit-logs/my-activity/data-modifications", response_model=List[AuditLogResponse])
async def get_my_data_modifications(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    resource_type: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get authenticated user's data modifications (create, update, delete).

    Helps users see what they've modified recently.
    """
    logs = AuditService.get_user_data_modifications(
        db,
        user_id=user_id,
        resource_type=resource_type,
        days=days,
        limit=limit,
    )
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "operation": log.operation,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "client_ip": log.client_ip,
            "endpoint": log.endpoint,
            "status": log.status,
            "status_code": log.status_code,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/audit-logs/my-activity/logins", response_model=List[AuditLogResponse])
async def get_my_logins(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get authenticated user's login history.

    Helps users see login activity and detect unauthorized access.
    """
    logs = (
        db.query(AuditLog)
        .filter(
            AuditLog.user_id == user_id,
            AuditLog.operation == "login",
        )
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "operation": log.operation,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "client_ip": log.client_ip,
            "endpoint": log.endpoint,
            "status": log.status,
            "status_code": log.status_code,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.post("/audit-logs/export")
async def export_activity(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    format: str = Query("json", regex="^(json|csv)$"),
    days: int = Query(30, ge=1, le=365),
):
    """
    Export authenticated user's activity logs.

    Supports JSON and CSV formats for data portability.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    export_data = AuditService.export_logs(
        db,
        user_id=user_id,
        start_date=start_date,
        format=format,
    )

    # Determine content type and filename
    if format == "json":
        content_type = "application/json"
        filename = f"audit_logs_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    else:  # csv
        content_type = "text/csv"
        filename = f"audit_logs_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return {
        "filename": filename,
        "format": format,
        "export_date": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "data": export_data,
    }


@router.get("/audit-logs/suspicious-activity", response_model=dict)
async def check_suspicious_activity(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check if authenticated user has suspicious activity on their account.

    Returns:
    - failed_logins: Recent failed login attempts
    - unusual_activity: Data modifications from unusual IPs
    """
    # Get failed logins in last 24 hours
    failed_logins = AuditService.get_failed_logins(
        db,
        client_ip=None,
        minutes=1440,  # 24 hours
        limit=50,
    )

    # Filter to this user's failed logins
    user_failed_logins = [
        log for log in failed_logins
        if log.user_id == user_id or (log.user_id is None and log.endpoint == "POST /api/auth/login")
    ]

    # Get user's recent activity from different IPs
    recent_activity = AuditService.get_user_activity(
        db,
        user_id=user_id,
        days=7,
        limit=100,
    )

    # Find unusual IPs (IPs that appear only once or twice)
    ip_counts = {}
    for log in recent_activity:
        if log.client_ip:
            ip_counts[log.client_ip] = ip_counts.get(log.client_ip, 0) + 1

    unusual_ips = [
        ip for ip, count in ip_counts.items()
        if count <= 2
    ]

    unusual_activity = [
        log for log in recent_activity
        if log.client_ip in unusual_ips
    ]

    return {
        "failed_logins": [
            {
                "timestamp": log.created_at.isoformat() if log.created_at else None,
                "ip": log.client_ip,
                "message": log.error_message or "Failed login attempt",
            }
            for log in user_failed_logins[-10:]  # Last 10 failures
        ],
        "unusual_activity": [
            {
                "timestamp": log.created_at.isoformat() if log.created_at else None,
                "operation": log.operation,
                "resource": f"{log.resource_type}:{log.resource_id}",
                "ip": log.client_ip,
            }
            for log in unusual_activity[-10:]  # Last 10 unusual activities
        ],
        "summary": {
            "total_failed_logins_24h": len(user_failed_logins),
            "unique_ips_7d": len(ip_counts),
            "unusual_ips": len(unusual_ips),
            "requires_attention": len(user_failed_logins) > 3 or len(unusual_ips) > 2,
        },
    }
