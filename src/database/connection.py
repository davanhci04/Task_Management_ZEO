from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import ZODB
import ZODB.config
from persistent import Persistent
from persistent.mapping import PersistentMapping
import transaction

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
        
    def connect(self):
        """Kết nối tới ZEO server"""
        try:
            # Kết nối tới ZEO server
            import ZEO
            self.db = ZEO.DB(('127.0.0.1', 8090))
            self.connection = self.db.open()
            self.root = self.connection.root()
            
            # Khởi tạo cấu trúc dữ liệu nếu chưa có
            if 'users' not in self.root:
                self.root['users'] = PersistentMapping()
                transaction.commit()
                
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False
    
    def reload_connection(self):
        """Reload connection để sync với ZEO server"""
        try:
            if self.connection:
                # Sync với server để lấy dữ liệu mới nhất
                self.connection.sync()
                # Cập nhật root object
                self.root = self.connection.root()
            return True
        except Exception as e:
            print(f"Reload connection error: {e}")
            return False
    
    def invalidate_cache(self):
        """Invalidate cache để force reload từ server"""
        try:
            if self.connection:
                self.connection.cacheMinimize()
                self.connection.sync()
            return True
        except Exception as e:
            print(f"Cache invalidation error: {e}")
            return False
    
    def close(self):
        """Đóng kết nối"""
        if self.connection:
            self.connection.close()
        if self.db:
            self.db.close()
    
    def get_root(self):
        # Sync trước khi trả về root để đảm bảo dữ liệu mới nhất
        self.reload_connection()
        return self.root

# Singleton instance
db_connection = DatabaseConnection()