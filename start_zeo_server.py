#!/usr/bin/env python3
"""
Script để khởi động ZEO server với cấu hình từ .env
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_zeo_config():
    """Tạo file cấu hình ZEO động từ .env (simplified)"""
    listen_host = os.getenv('LISTEN_HOST', '0.0.0.0')
    listen_port = os.getenv('LISTEN_PORT', '8090')
    
    # Config đơn giản hơn, loại bỏ các tùy chọn không hỗ trợ
    config_content = f"""
<zeo>
  address {listen_host}:{listen_port}
  read-only false
  invalidation-queue-size 100
</zeo>

<filestorage 1>
  path data/Data.fs
</filestorage>

<eventlog>
  level info
  <logfile>
    path logs/zeo.log
  </logfile>
</eventlog>
"""
    
    # Ghi config vào file
    with open('zeo_runtime.conf', 'w') as f:
        f.write(config_content)
    
    return 'zeo_runtime.conf'

def start_zeo_server():
    """Khởi động ZEO server"""
    # Tạo thư mục cần thiết
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Lấy config từ .env
    listen_host = os.getenv('LISTEN_HOST', '0.0.0.0')
    listen_port = os.getenv('LISTEN_PORT', '8090')
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    print("🚀 Starting ZEO Server...")
    print(f"📡 Listen Address: {listen_host}:{listen_port}")
    print(f"🗃️ Database: data/Data.fs")
    print(f"📝 Logs: logs/zeo.log")
    
    if debug:
        print("🐛 Debug mode: ON")
    
    # Thử phương pháp đơn giản nhất trước
    try:
        print("🔄 Method 1: Direct command line...")
        import subprocess
        
        cmd = [
            sys.executable, '-m', 'ZEO.runzeo',
            '-a', f'{listen_host}:{listen_port}',
            '-f', 'data/Data.fs'
        ]
        
        print(f"📝 Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Method 1 failed: {e}")
        print("🔄 Method 2: Using config file...")
        
        try:
            # Tạo config file đơn giản
            config_file = create_zeo_config()
            print(f"⚙️ Config file: {config_file}")
            
            cmd = [
                sys.executable, '-m', 'ZEO.runzeo',
                '-C', config_file
            ]
            
            print(f"📝 Running: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            
        except Exception as e:
            print(f"❌ Method 2 failed: {e}")
            print("🔄 Method 3: Manual server setup...")
            manual_start_server(listen_host, listen_port)
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("🔄 Trying manual server setup...")
        manual_start_server(listen_host, listen_port)

def manual_start_server(host, port):
    """Khởi động server thủ công"""
    try:
        print("🔧 Setting up ZEO server manually...")
        
        # Import các module cần thiết
        from ZODB.FileStorage import FileStorage
        from ZEO.StorageServer import StorageServer
        import threading
        import time
        import signal
        
        # Tạo file storage
        storage = FileStorage('data/Data.fs')
        print("✅ Created file storage")
        
        # Tạo ZEO server
        addr = (host, int(port))
        server = StorageServer(addr, {'1': storage})
        print(f"✅ ZEO server created on {host}:{port}")
        
        # Setup signal handler để đóng server gracefully
        def signal_handler(signum, frame):
            print("\n🛑 Received shutdown signal...")
            server.close()
            storage.close()
            print("✅ Server stopped gracefully")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print("🚀 ZEO server is running...")
        print("📡 Accepting connections...")
        print("🛑 Press Ctrl+C to stop")
        
        try:
            # Keep server running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            signal_handler(signal.SIGINT, None)
            
    except Exception as e:
        print(f"❌ Manual setup failed: {e}")
        print("💡 Please try installing ZEO again: pip install --upgrade ZEO")

if __name__ == "__main__":
    start_zeo_server()