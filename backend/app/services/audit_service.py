"""
Audit Service

Handles logging of sensitive operations for compliance and security monitoring.
Thread-safe implementation with automatic log rotation and cleanup.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service for managing audit logs."""

    @staticmethod
    def log_login_attempt(
        db: Session,
        username: str = None,
        user_id: str = None,
        client_ip: str = None,
        status: str = "success",
        error_message: str = None,
        user_agent: str = None,
    ) -> AuditLog:
        """
        Log authentication attempt.

        Args:
            db: Database session
            username: Username attempted (for failed logins)
            user_id: User ID if successful
            client_ip: Client IP address
            status: Operation status (success, failure, rate_limited)
            error_message: Error message if failed
            user_agent: User-Agent header

        Returns:
            Created audit log entry
        """
        log = AuditLog.create_login_attempt(
            user_id=user_id,
            client_ip=client_ip,
            status=status,
            error_message=error_message,
            user_agent=user_agent,
        )
        db.add(log)
        db.commit()

        logger.info(
            f"Login attempt: user_id={user_id}, ip={client_ip}, status={status}"
        )

        return log

    @staticmethod
    def log_data_operation(
        db: Session,
        user_id: str,
        operation: str,  # create, update, delete, read
        resource_type: str,  # payment, account, card, subscription, etc
        resource_id: str = None,
        client_ip: str = None,
        endpoint: str = None,
        status: str = "success",
        status_code: int = None,
        changes: Optional[Dict[str, Any]] = None,
        error_message: str = None,
        user_agent: str = None,
    ) -> AuditLog:
        """
        Log data modification operation.

        Args:
            db: Database session
            user_id: User performing operation
            operation: Operation type (create, update, delete)
            resource_type: Type of resource modified
            resource_id: ID of affected resource
            client_ip: Client IP address
            endpoint: API endpoint called
            status: Operation status
            status_code: HTTP status code
            changes: Dict of field changes (for updates)
            error_message: Error message if failed
            user_agent: User-Agent header

        Returns:
            Created audit log entry
        """
        log = AuditLog.create_data_operation(
            user_id=user_id,
            operation=operation,
            resource_type=resource_type,
            resource_id=resource_id,
            client_ip=client_ip,
            endpoint=endpoint,
            status=status,
            status_code=status_code,
            changes=changes,
            error_message=error_message,
            user_agent=user_agent,
        )
        db.add(log)
        db.commit()

        logger.info(
            f"Data operation: user_id={user_id}, operation={operation}, "
            f"resource={resource_type}:{resource_id}, status={status}"
        )

        return log

    @staticmethod
    def log_security_event(
        db: Session,
        event_type: str,  # rate_limit, unauthorized_access, csrf_failure, injection_attempt
        user_id: str = None,
        client_ip: str = None,
        resource_type: str = None,
        endpoint: str = None,
        details: str = None,
        user_agent: str = None,
    ) -> AuditLog:
        """
        Log security event (attacks, violations, suspicious activity).

        Args:
            db: Database session
            event_type: Type of security event
            user_id: User involved (if authenticated)
            client_ip: Client IP address
            resource_type: Resource involved
            endpoint: API endpoint
            details: Event details
            user_agent: User-Agent header

        Returns:
            Created audit log entry
        """
        log = AuditLog.create_security_event(
            event_type=event_type,
            user_id=user_id,
            client_ip=client_ip,
            resource_type=resource_type,
            endpoint=endpoint,
            details=details,
            user_agent=user_agent,
        )
        db.add(log)
        db.commit()

        logger.warning(
            f"Security event: type={event_type}, ip={client_ip}, "
            f"user_id={user_id}, endpoint={endpoint}"
        )

        return log

    @staticmethod
    def get_user_activity(
        db: Session,
        user_id: str,
        days: int = 30,
        limit: int = 100,
    ) -> list:
        """
        Get audit log entries for a user.

        Args:
            db: Database session
            user_id: User to fetch logs for
            days: Number of days to look back
            limit: Maximum number of entries to return

        Returns:
            List of audit log entries
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        logs = (
            db.query(AuditLog)
            .filter(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.created_at >= cutoff_date,
                )
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
        return logs

    @staticmethod
    def get_failed_logins(
        db: Session,
        client_ip: str = None,
        minutes: int = 60,
        limit: int = 100,
    ) -> list:
        """
        Get failed login attempts.

        Useful for detecting brute force attacks from specific IP.

        Args:
            db: Database session
            client_ip: Filter by client IP (optional)
            minutes: Time window to look back
            limit: Maximum number of entries to return

        Returns:
            List of failed login audit entries
        """
        cutoff_date = datetime.utcnow() - timedelta(minutes=minutes)
        query = db.query(AuditLog).filter(
            and_(
                AuditLog.operation == "login",
                AuditLog.status == "failure",
                AuditLog.created_at >= cutoff_date,
            )
        )

        if client_ip:
            query = query.filter(AuditLog.client_ip == client_ip)

        logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
        return logs

    @staticmethod
    def get_security_events(
        db: Session,
        event_type: str = None,
        client_ip: str = None,
        days: int = 7,
        limit: int = 100,
    ) -> list:
        """
        Get security events (attacks, suspicious activity).

        Args:
            db: Database session
            event_type: Filter by event type (optional)
            client_ip: Filter by client IP (optional)
            days: Number of days to look back
            limit: Maximum number of entries to return

        Returns:
            List of security event audit entries
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = db.query(AuditLog).filter(
            and_(
                AuditLog.status == "security_event",
                AuditLog.created_at >= cutoff_date,
            )
        )

        if event_type:
            query = query.filter(AuditLog.operation == event_type)

        if client_ip:
            query = query.filter(AuditLog.client_ip == client_ip)

        logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
        return logs

    @staticmethod
    def get_user_data_modifications(
        db: Session,
        user_id: str,
        resource_type: str = None,
        days: int = 30,
        limit: int = 100,
    ) -> list:
        """
        Get data modifications by a user.

        Args:
            db: Database session
            user_id: User to fetch modifications for
            resource_type: Filter by resource type (optional)
            days: Number of days to look back
            limit: Maximum number of entries to return

        Returns:
            List of data modification audit entries
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = db.query(AuditLog).filter(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.operation.in_(["create", "update", "delete"]),
                AuditLog.created_at >= cutoff_date,
            )
        )

        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)

        logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
        return logs

    @staticmethod
    def cleanup_old_logs(db: Session, days: int = 90) -> int:
        """
        Delete audit logs older than specified days.

        Helps manage database size while retaining recent audit trail.
        Should be called periodically (e.g., daily cron job).

        Args:
            db: Database session
            days: Age threshold for deletion (default 90 days)

        Returns:
            Number of deleted entries
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = (
            db.query(AuditLog)
            .filter(AuditLog.created_at < cutoff_date)
            .delete()
        )
        db.commit()

        logger.info(f"Cleaned up {deleted_count} audit logs older than {days} days")
        return deleted_count

    @staticmethod
    def get_suspicious_ips(
        db: Session,
        min_failed_logins: int = 5,
        minutes: int = 60,
    ) -> list:
        """
        Find IPs with multiple failed login attempts.

        Useful for identifying brute force attacks.

        Args:
            db: Database session
            min_failed_logins: Minimum number of failures to flag
            minutes: Time window to check

        Returns:
            List of (IP, failed_count) tuples
        """
        cutoff_date = datetime.utcnow() - timedelta(minutes=minutes)
        from sqlalchemy import func

        suspicious = (
            db.query(
                AuditLog.client_ip,
                func.count(AuditLog.id).label("failed_count"),
            )
            .filter(
                and_(
                    AuditLog.operation == "login",
                    AuditLog.status == "failure",
                    AuditLog.created_at >= cutoff_date,
                )
            )
            .group_by(AuditLog.client_ip)
            .having(func.count(AuditLog.id) >= min_failed_logins)
            .order_by(func.count(AuditLog.id).desc())
            .all()
        )

        return suspicious

    @staticmethod
    def export_logs(
        db: Session,
        user_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        format: str = "json",
    ) -> str:
        """
        Export audit logs in specified format.

        Args:
            db: Database session
            user_id: Filter by user (optional)
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            format: Export format ('json' or 'csv')

        Returns:
            Exported logs as string
        """
        query = db.query(AuditLog)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)

        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        logs = query.order_by(AuditLog.created_at.desc()).all()

        if format == "json":
            return json.dumps([log.to_dict() for log in logs], indent=2, default=str)
        elif format == "csv":
            import csv
            from io import StringIO

            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                "id", "user_id", "operation", "resource_type", "resource_id",
                "client_ip", "endpoint", "status", "status_code", "created_at"
            ])
            writer.writeheader()
            for log in logs:
                writer.writerow(log.to_dict())
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")
