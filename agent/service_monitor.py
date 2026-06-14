import subprocess
import shutil
import logging

logger = logging.getLogger("infrawatch.agent.service_monitor")

def get_service_status(service_name: str) -> str:
    """
    Checks if a Linux systemd service is active using `systemctl is-active <service_name>`.
    Returns "active" if it is running, otherwise "down".
    If systemctl is not available (e.g. non-Linux systems), returns "down" and logs a warning.
    """
    # Check if systemctl executable is present in PATH
    if not shutil.which("systemctl"):
        logger.warning(
            f"systemctl command not found. Cannot determine status for '{service_name}'. "
            "Defaulting status to 'down'."
        )
        return "down"

    try:
        # Run systemctl is-active command
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
            check=False
        )
        status = result.stdout.strip()
        
        if status == "active":
            return "active"
        else:
            logger.info(f"Service '{service_name}' status reported as: '{status}'")
            return "down"
            
    except Exception as e:
        logger.error(f"Error checking status for service '{service_name}': {str(e)}")
        return "down"
