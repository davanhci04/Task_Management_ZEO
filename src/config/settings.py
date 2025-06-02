import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_CONFIG = {
    'host': os.getenv('ZEO_HOST', '127.0.0.1'),
    'port': int(os.getenv('ZEO_PORT', 8090)),
    'timeout': int(os.getenv('CONNECTION_TIMEOUT', 30))
}

NETWORK_CONFIG = {
    'listen_host': os.getenv('LISTEN_HOST', '0.0.0.0'),
    'listen_port': int(os.getenv('LISTEN_PORT', 8090)),
    'auto_refresh_interval': int(os.getenv('AUTO_REFRESH_INTERVAL', 3000)),
    'retry_attempts': int(os.getenv('RETRY_ATTEMPTS', 3)),
    'retry_delay': int(os.getenv('RETRY_DELAY', 5))
}

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

def get_server_address():
    """Lấy địa chỉ server để client kết nối"""
    return (DATABASE_CONFIG['host'], DATABASE_CONFIG['port'])

def get_listen_address():
    """Lấy địa chỉ để ZEO server listen"""
    return (NETWORK_CONFIG['listen_host'], NETWORK_CONFIG['listen_port'])

def print_config():
    """In ra cấu hình hiện tại (để debug)"""
    if DEBUG:
        print("=== CONFIGURATION ===")
        print(f"ZEO Host: {DATABASE_CONFIG['host']}")
        print(f"ZEO Port: {DATABASE_CONFIG['port']}")
        print(f"Listen Host: {NETWORK_CONFIG['listen_host']}")
        print(f"Listen Port: {NETWORK_CONFIG['listen_port']}")
        print(f"Auto Refresh: {NETWORK_CONFIG['auto_refresh_interval']}ms")
        print("====================")