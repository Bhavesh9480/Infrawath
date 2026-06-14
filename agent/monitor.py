import time
import datetime
import logging
import os
import re
import requests
import psutil

import config
import service_monitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] agent.monitor: %(message)s"
)
logger = logging.getLogger("infrawatch.agent")

class AuthLogParser:
    def __init__(self, log_path: str):
        self.log_path = log_path
        self.last_position = None
        self.file_inode = None
        self.logged_warning = False

    def _reset_position(self):
        """
        Attempts to open the file and seek to the end.
        Ensures we only read new lines appended after the agent starts.
        """
        if not os.path.exists(self.log_path):
            if not self.logged_warning:
                logger.warning(f"Auth log file not found at: '{self.log_path}'. Security monitoring disabled.")
                self.logged_warning = True
            return False

        try:
            stat_info = os.stat(self.log_path)
            self.file_inode = stat_info.st_ino
            
            with open(self.log_path, 'r', errors='ignore') as f:
                f.seek(0, os.SEEK_END)
                self.last_position = f.tell()
            
            self.logged_warning = False
            return True
        except PermissionError:
            if not self.logged_warning:
                logger.warning(f"Permission denied reading '{self.log_path}'. Run agent with sudo to monitor security logs.")
                self.logged_warning = True
            return False
        except Exception as e:
            logger.error(f"Error initializing auth log parsing: {str(e)}")
            return False

    def parse_new_failed_logins(self):
        """
        Reads any new lines in the auth log since the last check.
        Scans for authentication failure patterns.
        """
        if not os.path.exists(self.log_path):
            return []

        # Check if the log file has been rotated or position needs initialization
        try:
            stat_info = os.stat(self.log_path)
            current_inode = stat_info.st_ino
            
            if self.last_position is None or self.file_inode != current_inode:
                logger.info("Initializing or re-initializing auth log reader position.")
                success = self._reset_position()
                if not success:
                    return []
        except (PermissionError, FileNotFoundError):
            return []

        failed_logins = []
        try:
            with open(self.log_path, 'r', errors='ignore') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()

            for line in new_lines:
                line_lower = line.lower()
                # Detection patterns: "Failed password", "Invalid user", "Authentication failure"
                if ("failed password" in line_lower or 
                    "invalid user" in line_lower or 
                    "authentication failure" in line_lower):
                    
                    parsed_ts = self._extract_timestamp(line)
                    failed_logins.append({
                        "timestamp": parsed_ts.isoformat(),
                        "message": line.strip()
                    })

        except PermissionError:
            pass # Silently pass if permissions are revoked mid-run
        except Exception as e:
            logger.error(f"Error parsing auth log: {str(e)}")

        return failed_logins

    def _extract_timestamp(self, line: str) -> datetime.datetime:
        """
        Extracts the timestamp from a syslog line.
        Supports standard syslog formats (e.g. 'Jun 13 14:55:01' or ISO-8601).
        Falls back to current system time if parsing fails.
        """
        now = datetime.datetime.utcnow()
        
        # 1. Try to match ISO-8601 timestamp (e.g., 2026-06-13T14:55:01.123456+05:30)
        iso_match = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", line)
        if iso_match:
            try:
                return datetime.datetime.fromisoformat(iso_match.group(1))
            except ValueError:
                pass

        # 2. Try to match traditional syslog format (e.g., Jun 13 14:55:01)
        syslog_match = re.match(r"^([A-Z][a-z]{2})\s+(\d+)\s+(\d{2}:\d{2}:\d{2})", line)
        if syslog_match:
            try:
                month_str, day_str, time_str = syslog_match.groups()
                # Prepend the current year since syslog doesn't include it
                ts_str = f"{now.year} {month_str} {int(day_str):02d} {time_str}"
                return datetime.datetime.strptime(ts_str, "%Y %b %d %H:%M:%S")
            except ValueError:
                pass

        # Fallback to current time
        return now

def gather_metrics(log_parser: AuthLogParser) -> dict:
    """
    Gathers host system metrics, service statuses, and parsed failed login attempts.
    """
    # CPU usage over a 1-second sample
    cpu_percent = psutil.cpu_percent(interval=1.0)
    # Memory usage
    memory_percent = psutil.virtual_memory().percent
    # Disk usage (root mountpoint)
    disk_percent = psutil.disk_usage('/').percent
    
    # Network metrics (bytes sent/received)
    try:
        net_io = psutil.net_io_counters()
        bytes_sent = net_io.bytes_sent
        bytes_recv = net_io.bytes_recv
    except Exception as e:
        logger.warning(f"Failed to fetch network IO metrics: {str(e)}")
        bytes_sent = 0
        bytes_recv = 0

    # Service health checks
    services_status = []
    for svc in config.SERVICES:
        status = service_monitor.get_service_status(svc)
        services_status.append({
            "service_name": svc,
            "status": status
        })

    # Failed login attempts
    failed_logins = log_parser.parse_new_failed_logins()

    return {
        "server_name": config.SERVER_NAME,
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "disk_percent": disk_percent,
        "bytes_sent": bytes_sent,
        "bytes_recv": bytes_recv,
        "services": services_status,
        "failed_logins": failed_logins
    }

def main():
    logger.info(f"Starting InfraWatch Host Agent on '{config.SERVER_NAME}'...")
    logger.info(f"Target Backend API: '{config.BACKEND_URL}'")
    logger.info(f"Check Interval: {config.INTERVAL} seconds")
    logger.info(f"Monitored Services: {config.SERVICES}")

    log_parser = AuthLogParser(config.AUTH_LOG_PATH)
    
    # Run loop
    while True:
        try:
            start_time = time.time()
            
            # Gather statistics
            payload = gather_metrics(log_parser)
            logger.info(
                f"Ingested metrics - CPU: {payload['cpu_percent']}%, "
                f"RAM: {payload['memory_percent']}%, "
                f"Disk: {payload['disk_percent']}%"
            )

            # Send payload to backend
            try:
                response = requests.post(
                    config.BACKEND_URL,
                    json=payload,
                    timeout=5
                )
                if response.status_code == 201:
                    logger.info("Metrics payload successfully posted to backend.")
                else:
                    logger.error(
                        f"Backend rejected metrics with status code {response.status_code}: "
                        f"{response.text}"
                    )
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to connect to backend server: {str(e)}")

            # Calculate remaining sleep time to match exact 15-second cycles
            elapsed = time.time() - start_time
            sleep_time = max(0.1, config.INTERVAL - elapsed)
            time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("Agent process interrupted by user. Exiting...")
            break
        except Exception as e:
            logger.critical(f"Unexpected error in main agent daemon loop: {str(e)}")
            time.sleep(config.INTERVAL)

if __name__ == "__main__":
    main()

