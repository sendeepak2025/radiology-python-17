"""
Alert configuration for Kiro-mini monitoring system.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    metric_name: str
    threshold: float
    comparison: str = "greater_than"
    duration: int = 60
    severity: str = "warning"
    description: str = ""
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}


class AlertConfiguration:
    """Central configuration for all alert rules."""
    
    @staticmethod
    def get_default_alert_rules() -> List[AlertRule]:
        """Get default alert rules for Kiro-mini."""
        return [
            # Performance Alerts
            AlertRule(
                name="high_response_time",
                metric_name="http_request_duration_ms",
                threshold=5000,  # 5 seconds
                comparison="greater_than",
                duration=120,  # 2 minutes
                severity="warning",
                description="API response time is consistently high"
            ),
            
            AlertRule(
                name="critical_response_time",
                metric_name="http_request_duration_ms",
                threshold=10000,  # 10 seconds
                comparison="greater_than",
                duration=60,  # 1 minute
                severity="critical",
                description="API response time is critically high"
            ),
            
            AlertRule(
                name="high_error_rate",
                metric_name="http_errors_total",
                threshold=0.05,  # 5% error rate
                comparison="greater_than",
                duration=60,
                severity="warning",
                description="HTTP error rate is elevated"
            ),
            
            AlertRule(
                name="critical_error_rate",
                metric_name="http_errors_total",
                threshold=0.15,  # 15% error rate
                comparison="greater_than",
                duration=30,
                severity="critical",
                description="HTTP error rate is critically high"
            ),
            
            # System Resource Alerts
            AlertRule(
                name="high_cpu_usage",
                metric_name="system_cpu_percent",
                threshold=80,  # 80%
                comparison="greater_than",
                duration=300,  # 5 minutes
                severity="warning",
                description="CPU usage is consistently high"
            ),
            
            AlertRule(
                name="critical_cpu_usage",
                metric_name="system_cpu_percent",
                threshold=95,  # 95%
                comparison="greater_than",
                duration=60,
                severity="critical",
                description="CPU usage is critically high"
            ),
            
            AlertRule(
                name="high_memory_usage",
                metric_name="system_memory_percent",
                threshold=85,  # 85%
                comparison="greater_than",
                duration=300,
                severity="warning",
                description="Memory usage is consistently high"
            ),
            
            AlertRule(
                name="critical_memory_usage",
                metric_name="system_memory_percent",
                threshold=95,  # 95%
                comparison="greater_than",
                duration=60,
                severity="critical",
                description="Memory usage is critically high"
            ),
            
            AlertRule(
                name="low_disk_space",
                metric_name="system_disk_percent",
                threshold=85,  # 85%
                comparison="greater_than",
                duration=600,  # 10 minutes
                severity="warning",
                description="Disk space is running low"
            ),
            
            AlertRule(
                name="critical_disk_space",
                metric_name="system_disk_percent",
                threshold=95,  # 95%
                comparison="greater_than",
                duration=60,
                severity="critical",
                description="Disk space is critically low"
            ),
            
            # Application-Specific Alerts
            AlertRule(
                name="ai_processing_queue_backlog",
                metric_name="ai_queue_pending_jobs",
                threshold=50,
                comparison="greater_than",
                duration=300,
                severity="warning",
                description="AI processing queue has significant backlog"
            ),
            
            AlertRule(
                name="ai_processing_failures",
                metric_name="ai_processing_failures",
                threshold=5,
                comparison="greater_than",
                duration=300,
                severity="warning",
                description="Multiple AI processing failures detected"
            ),
            
            AlertRule(
                name="database_connection_failures",
                metric_name="database_connection_errors",
                threshold=3,
                comparison="greater_than",
                duration=60,
                severity="critical",
                description="Database connection failures detected"
            ),
            
            AlertRule(
                name="redis_connection_failures",
                metric_name="redis_connection_errors",
                threshold=3,
                comparison="greater_than",
                duration=60,
                severity="critical",
                description="Redis connection failures detected"
            ),
            
            # Workflow Performance Alerts
            AlertRule(
                name="slow_study_ingestion",
                metric_name="study_ingestion_duration_ms",
                threshold=5000,  # 5 seconds
                comparison="greater_than",
                duration=120,
                severity="warning",
                description="Study ingestion is taking too long"
            ),
            
            AlertRule(
                name="slow_report_generation",
                metric_name="report_generation_duration_ms",
                threshold=60000,  # 60 seconds (1 minute target)
                comparison="greater_than",
                duration=60,
                severity="critical",
                description="Report generation exceeding 1-minute target"
            ),
            
            AlertRule(
                name="slow_billing_generation",
                metric_name="billing_generation_duration_ms",
                threshold=10000,  # 10 seconds
                comparison="greater_than",
                duration=120,
                severity="warning",
                description="Billing generation is taking too long"
            ),
            
            # External Service Alerts
            AlertRule(
                name="orthanc_connection_failure",
                metric_name="orthanc_health_check_failures",
                threshold=2,
                comparison="greater_than",
                duration=120,
                severity="critical",
                description="Orthanc DICOM server is not responding"
            ),
            
            AlertRule(
                name="ai_service_connection_failure",
                metric_name="ai_service_health_check_failures",
                threshold=2,
                comparison="greater_than",
                duration=120,
                severity="critical",
                description="AI service is not responding"
            ),
            
            # Business Logic Alerts
            AlertRule(
                name="high_billing_validation_failures",
                metric_name="billing_validation_failures",
                threshold=10,
                comparison="greater_than",
                duration=300,
                severity="warning",
                description="High number of billing validation failures"
            ),
            
            AlertRule(
                name="webhook_delivery_failures",
                metric_name="webhook_delivery_failures",
                threshold=5,
                comparison="greater_than",
                duration=300,
                severity="warning",
                description="Multiple webhook delivery failures"
            ),
            
            AlertRule(
                name="audit_log_failures",
                metric_name="audit_log_failures",
                threshold=1,
                comparison="greater_than",
                duration=60,
                severity="critical",
                description="Audit logging failures detected (compliance risk)"
            ),
            
            # Security Alerts
            AlertRule(
                name="high_authentication_failures",
                metric_name="authentication_failures",
                threshold=20,
                comparison="greater_than",
                duration=300,
                severity="warning",
                description="High number of authentication failures"
            ),
            
            AlertRule(
                name="suspicious_access_patterns",
                metric_name="suspicious_access_attempts",
                threshold=5,
                comparison="greater_than",
                duration=60,
                severity="critical",
                description="Suspicious access patterns detected"
            ),
        ]
    
    @staticmethod
    def get_alert_channels() -> Dict[str, Dict[str, Any]]:
        """Get alert notification channel configurations."""
        return {
            "webhook": {
                "enabled": True,
                "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
                "timeout": 10,
                "retry_attempts": 3
            },
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "alerts@yourdomain.com",
                "password": "your_password",
                "recipients": ["admin@yourdomain.com", "ops@yourdomain.com"]
            },
            "pagerduty": {
                "enabled": False,
                "integration_key": "your_pagerduty_integration_key",
                "severity_mapping": {
                    "critical": "critical",
                    "warning": "warning",
                    "info": "info"
                }
            }
        }
    
    @staticmethod
    def get_alert_templates() -> Dict[str, str]:
        """Get alert message templates."""
        return {
            "firing": """
🚨 **ALERT FIRING** 🚨

**Alert:** {alert_name}
**Severity:** {severity}
**Description:** {description}

**Metric:** {metric_name}
**Current Value:** {current_value}
**Threshold:** {threshold} ({comparison})
**Duration:** {duration}s

**Timestamp:** {timestamp}
**Environment:** {environment}

**Actions:**
- Check system health: /health/detailed
- View metrics: /health/metrics
- Check logs for errors
            """.strip(),
            
            "resolved": """
✅ **ALERT RESOLVED** ✅

**Alert:** {alert_name}
**Severity:** {severity}
**Description:** {description}

**Metric:** {metric_name}
**Current Value:** {current_value}
**Threshold:** {threshold} ({comparison})

**Resolved At:** {timestamp}
**Environment:** {environment}

The issue has been automatically resolved.
            """.strip()
        }
    
    @staticmethod
    def get_escalation_rules() -> List[Dict[str, Any]]:
        """Get alert escalation rules."""
        return [
            {
                "severity": "critical",
                "escalation_delay": 300,  # 5 minutes
                "channels": ["webhook", "pagerduty"],
                "repeat_interval": 900  # 15 minutes
            },
            {
                "severity": "warning",
                "escalation_delay": 600,  # 10 minutes
                "channels": ["webhook"],
                "repeat_interval": 1800  # 30 minutes
            },
            {
                "severity": "info",
                "escalation_delay": 1800,  # 30 minutes
                "channels": ["email"],
                "repeat_interval": 3600  # 1 hour
            }
        ]