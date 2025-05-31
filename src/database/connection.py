from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import ZODB
import ZODB.config
from persistent import Persistent
from persistent.mapping import PersistentMapping
import transaction
import time
from config.settings import DATABASE_CONFIG, NETWORK_CONFIG, DEBUG

DATABASE_URL = "sqlite:///tasks.db"  # Update with your database URL

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()

def close_session(session):
    session.close()

class DatabaseConnection:
    def __init__(self):
        self.db = None
        self.connection = None
        self.root = None
        
    def connect(self, server_host=None, server_port=None):
        """Kết nối tới ZEO server với retry logic"""
        # Sử dụng config từ .env hoặc tham số truyền vào
        host = server_host or DATABASE_CONFIG['host']
        port = server_port or DATABASE_CONFIG['port']
        
        retry_attempts = NETWORK_CONFIG['retry_attempts']
        retry_delay = NETWORK_CONFIG['retry_delay']
        
        for attempt in range(retry_attempts):
            try:
                if DEBUG:
                    print(f"Attempt {attempt + 1}/{retry_attempts}: Connecting to ZEO server at {host}:{port}")
                
                # Kết nối tới ZEO server
                import ZEO
                self.db = ZEO.DB((host, port))
                self.connection = self.db.open()
                self.root = self.connection.root()
                
                # Khởi tạo cấu trúc dữ liệu nếu chưa có
                if 'users' not in self.root:
                    self.root['users'] = PersistentMapping()
                    transaction.commit()
                    if DEBUG:
                        print("Initialized database structure")
                
                if DEBUG:
                    print(f"✅ Successfully connected to ZEO server at {host}:{port}")
                return True
                
            except Exception as e:
                if DEBUG:
                    print(f"❌ Connection attempt {attempt + 1} failed: {e}")
                
                if attempt < retry_attempts - 1:
                    if DEBUG:
                        print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Failed to connect after {retry_attempts} attempts")
                    
        return False
    
    def reload_connection(self):
        """Reload connection để sync với ZEO server"""
        try:
            if self.connection:
                # Sync với server để lấy dữ liệu mới nhất
                self.connection.sync()
                # Cập nhật root object
                self.root = self.connection.root()
                if DEBUG:
                    print("🔄 Connection reloaded successfully")
            return True
        except Exception as e:
            if DEBUG:
                print(f"❌ Reload connection error: {e}")
            return False
    
    def invalidate_cache(self):
        """Invalidate cache để force reload từ server"""
        try:
            if self.connection:
                self.connection.cacheMinimize()
                self.connection.sync()
                if DEBUG:
                    print("🗑️ Cache invalidated and synced")
            return True
        except Exception as e:
            if DEBUG:
                print(f"❌ Cache invalidation error: {e}")
            return False
    
    def close(self):
        """Đóng kết nối"""
        try:
            if self.connection:
                self.connection.close()
                if DEBUG:
                    print("🔌 Database connection closed")
            if self.db:
                self.db.close()
        except Exception as e:
            if DEBUG:
                print(f"❌ Error closing connection: {e}")
    
    def get_root(self):
        """Lấy root object với sync"""
        # Sync trước khi trả về root để đảm bảo dữ liệu mới nhất
        self.reload_connection()
        return self.root
    
    def test_connection(self):
        """Test kết nối và in thông tin debug"""
        if DEBUG:
            try:
                root = self.get_root()
                user_count = len(root.get('users', {}))
                print(f"📊 Connection test: {user_count} users in database")
                return True
            except Exception as e:
                print(f"❌ Connection test failed: {e}")
                return False
        return self.connection is not None

# Singleton instance
db_connection = DatabaseConnection()