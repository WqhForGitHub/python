"""数据库引擎与 Session 配置。

使用 SQLite 作为开发数据库，启动时自动建表。
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite 数据库文件位于项目根目录
SQLALCHEMY_DATABASE_URL = "sqlite:///./crud_demo.db"

# SQLite 需要指定 connect_args 以支持多线程访问
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 所有 ORM 模型的基类
Base = declarative_base()


def get_db():
    """依赖项：每个请求获取一个独立的数据库 Session，请求结束后关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
