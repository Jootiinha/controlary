"""
Audit Log Model

Tracks all sensitive operations (logins, data modifications, permission changes)
for compliance, security monitoring, and incident investigation.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, Index
from sqlalchemy.sql import func

from app.database import Base


class AuditLog(Base):
    """
    Audit log entry for sensitive operations.

    Tracks:
    - User authentication (login, logout, failed attempts)
    - Data modifications (create, update, delete)
    - Permission changes
    - Error conditions and exceptions
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Operation metadata
    user_id = Column(String, nullable=True, index=True)  # NULL for unauthenticated operations
    operation = Column(String(50), nullable=False, index=True)  # login, create_payment, delete_account, etc
    resource_type = Column(String(50), nullable=False, index=True)  # payment, account, card, etc
    resource_id = Column(String, nullable=True, index=True)  # ID of affected resource

    # Request context
    client_ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    endpoint = Column(String, nullable=False)  # GET /api/payments, POST /api/auth/login, etc

    # Operation details
    status = Column(String(20), nullable=False, index=True)  # success, failure, rate_limited, unauthorized
    status_code = Column(Integer, nullable=True)  # HTTP status code
    details = Column(Text, nullable=True)  # JSON or text details of operation
    error_message = Column(Text, nullable=True)  # Error if operation failed

    # Sensitive data (encrypted in production)
    changes = Column(Text, nullable=True)  # JSON: {field: {old_value, new_value}} for updates

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    # Query indexes for common audit scenarios
    __table_args__ = (
        Index('idx_audit_user_date', 'user_id', 'created_at'),
        Index('idx_audit_operation_date', 'operation', 'created_at'),
        Index('idx_audit_status_date', 'status', 'created_at'),
        Index('idx_audit_ip_date', 'client_ip', 'created_at'),
    )

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "operation": self.operation,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "client_ip": self.client_ip,
            "endpoint": self.endpoint,
            "status": self.status,
            "status_code": self.status_code,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @staticmethod
    def create_login_attempt(
        user_id: str = None,
        client_ip: str = None,
        status: str = "success",
        error_message: str = None,
        user_agent: str = None
    ):
        """Create login attempt audit log."""
        return AuditLog(
            user_id=user_id,
            operation="login",
            resource_type="user",
            resource_id=user_id,
            client_ip=client_ip,
            user_agent=user_agent,
            endpoint="POST /api/auth/login",
            status=status,
            error_message=error_message,
        )

    @staticmethod
    def create_data_operation(
        user_id: str,
        operation: str,  # create, update, delete
        resource_type: str,  # payment, account, card, etc
        resource_id: str = None,
        client_ip: str = None,
        endpoint: str = None,
        status: str = "success",
        status_code: int = None,
        changes: dict = None,
        error_message: str = None,
        user_agent: str = None
    ):
        """Create data modification audit log."""
        import json
        return AuditLog(
            user_id=user_id,
            operation=operation,
            resource_type=resource_type,
            resource_id=resource_id,
            client_ip=client_ip,
            user_agent=user_agent,
            endpoint=endpoint or f"POST /api/{resource_type}s",
            status=status,
            status_code=status_code,
            changes=json.dumps(changes) if changes else None,
            error_message=error_message,
        )

    @staticmethod
    def create_security_event(
        event_type: str,  # rate_limit, unauthorized_access, csrf_failure, sql_injection_attempt
        user_id: str = None,
        client_ip: str = None,
        resource_type: str = None,
        endpoint: str = None,
        details: str = None,
        user_agent: str = None
    ):
        """Create security event audit log."""
        return AuditLog(
            user_id=user_id,
            operation=event_type,
            resource_type=resource_type or "system",
            client_ip=client_ip,
            user_agent=user_agent,
            endpoint=endpoint or "unknown",
            status="security_event",
            status_code=403,
            details=details,
        )
