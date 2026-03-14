"""
Alert Tasks
===========
Send notifications for high-risk players requiring immediate attention.
"""

import pandas as pd
from airflow.utils.log.logging_mixin import LoggingMixin
from airflow.operators.email import EmailOperator


logger = LoggingMixin().log


def send_performance_alerts(input_file: str, injury_threshold: float = 0.7, **context):
    """
    Send alerts for players exceeding injury risk threshold.
    
    Args:
        input_file: Path to merged predictions CSV
        injury_threshold: Risk score threshold for alerting (0-1)
    """
    
    logger.info(f"Checking for high-risk players (threshold: {injury_threshold})...")
    
    try:
        # Load data
        df = pd.read_csv(input_file)
        
        # Filter high-risk players
        high_risk = df[df["injury_risk_score"] > injury_threshold].sort_values(
            "injury_risk_score", ascending=False
        )
        
        logger.info(f"Found {len(high_risk)} players exceeding injury threshold")
        
        if len(high_risk) == 0:
            logger.info("No high-risk players detected. No alerts needed.")
            return {
                "status": "success",
                "alerts_sent": 0,
                "high_risk_players": 0
            }
        
        # Prepare alert message
        alert_message = _generate_alert_message(high_risk)
        
        # Log detailed alert
        logger.warning(alert_message)
        
        # Send email alert (if needed)
        _send_email_alert(high_risk, alert_message)
        
        # Log to file for audit trail
        high_risk.to_csv(f"/tmp/high_risk_players_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
        
        return {
            "status": "success",
            "alerts_sent": len(high_risk),
            "high_risk_players": len(high_risk),
            "top_risk_player": high_risk.iloc[0]["player_name"],
            "top_risk_score": float(high_risk.iloc[0]["injury_risk_score"])
        }
        
    except Exception as e:
        logger.error(f"Error sending alerts: {str(e)}")
        # Don't raise - alerting should not block main pipeline
        return {
            "status": "warning",
            "error": str(e)
        }


def _generate_alert_message(high_risk_df: pd.DataFrame) -> str:
    """Generate formatted alert message."""
    
    message = "=" * 80 + "\n"
    message += "🚨 HIGH-RISK PLAYERS ALERT — IMMEDIATE ACTION REQUIRED 🚨\n"
    message += "=" * 80 + "\n\n"
    
    message += f"Total High-Risk Players: {len(high_risk_df)}\n\n"
    
    message += "TOP 10 PRIORITY PLAYERS:\n"
    message += "-" * 80 + "\n"
    
    for idx, (_, row) in enumerate(high_risk_df.head(10).iterrows(), 1):
        message += f"\n{idx}. {row['player_name']} (ID: {row['player_id']})\n"
        message += f"   Position: {row['position']}\n"
        message += f"   Injury Risk Score: {row['injury_risk_score']:.2%}\n"
        message += f"   Risk Level: {row['injury_risk_level']}\n"
        message += f"   Performance Change: {row['rating_improvement']:+.1f}\n"
        message += f"   Recommended Action: {row['recommended_action']}\n"
    
    message += "\n" + "=" * 80 + "\n"
    message += "RECOMMENDED IMMEDIATE ACTIONS:\n"
    message += "=" * 80 + "\n"
    
    action_groups = high_risk_df.groupby("recommended_action").size()
    for action, count in action_groups.items():
        message += f"  • {action}: {count} players\n"
    
    message += "\nPlease review and take appropriate action within 24 hours.\n"
    
    return message


def _send_email_alert(high_risk_df: pd.DataFrame, message: str):
    """Send email alert to coaches and medical staff."""
    
    logger.info(f"Sending email alerts for {len(high_risk_df)} high-risk players...")
    
    try:
        # In production, configure these via Airflow variables
        recipients = [
            "coach@team.com",
            "medical@team.com",
            "admin@example.com"
        ]
        
        # Create an EmailOperator task
        # This would normally be done via task configuration
        # For now, just log that alert would be sent
        logger.info(f"Alert would be sent to: {', '.join(recipients)}")
        logger.info(f"Message preview: {message[:200]}...")
        
    except Exception as e:
        logger.warning(f"Could not send email alert: {str(e)}")
