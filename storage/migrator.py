"""
数据库 Schema 迁移管理器
支持增量迁移，确保用户数据安全
"""
import sqlite3
import uuid
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """数据库 Schema 迁移管理器"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    def get_current_version(self) -> int:
        """
        获取当前数据库 Schema 版本
        
        Returns:
            当前版本号，schema_version 表不存在时返回 0
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            row = cursor.fetchone()
            version = row[0] if row else 0
        except sqlite3.OperationalError:
            # schema_version 表不存在
            version = 0
        finally:
            conn.close()
        
        return version
    
    def migrate(self, target_version: int):
        """
        从当前版本逐步迁移到目标版本
        
        Args:
            target_version: 目标 Schema 版本号
        """
        current = self.get_current_version()
        
        if current >= target_version:
            logger.debug(f"Schema is up to date (v{current})")
            return
        
        logger.info(f"Schema migration needed: v{current} → v{target_version}")
        
        # 迁移方法映射表
        migrations = {
            1: self._migrate_to_v1,
            2: self._migrate_to_v2,
            3: self._migrate_to_v3,
        }
        
        # 逐步执行增量迁移
        for version in range(current + 1, target_version + 1):
            migration_fn = migrations.get(version)
            if migration_fn is None:
                logger.error(f"No migration script found for v{version}")
                raise RuntimeError(f"Missing migration script for schema v{version}")
            
            try:
                logger.info(f"Running migration to v{version}...")
                migration_fn()
                self._set_version(version)
                logger.info(f"Migration to v{version} completed successfully")
            except Exception as e:
                logger.error(f"Migration to v{version} failed: {e}", exc_info=True)
                raise
    
    def _set_version(self, version: int):
        """更新 schema_version 表中的版本号"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute(
                "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                (version,)
            )
            conn.commit()
        finally:
            conn.close()
    
    # ============================
    # 迁移脚本
    # ============================
    
    def _migrate_to_v1(self):
        """
        v0 → v1: 初始化 schema_version 表
        
        这是基线迁移。对于全新安装的用户，tasks 表已经由 Database.init_db() 创建。
        对于从旧版升级的用户，tasks 表已存在，此迁移仅添加版本跟踪。
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 创建 schema_version 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info("Created schema_version table")
        finally:
            conn.close()
    
    def _migrate_to_v2(self):
        """
        v1 → v2: 新增 task_type 列，默认为 'daily'
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE tasks ADD COLUMN task_type TEXT DEFAULT 'daily'")
            conn.commit()
            logger.info("Added task_type column to tasks table")
        except sqlite3.OperationalError as e:
            logger.warning(f"Failed to add task_type column (it may already exist): {e}")
        finally:
            conn.close()

    def _migrate_to_v3(self):
        """
        v2 → v3: 为 PC/手机双端同步准备字段。

        - 新增全局唯一 uuid、软删除墓碑、待推送标记、语音相关列
        - 给所有现有行回填 uuid，并标记为 dirty=1（首次同步时整批推送上云）
        """
        # 需要新增的列（列名 -> 建列 DDL 片段）
        new_columns = [
            ("uuid", "uuid TEXT"),
            ("deleted", "deleted INTEGER DEFAULT 0"),
            ("deleted_at", "deleted_at TIMESTAMP"),
            ("dirty", "dirty INTEGER DEFAULT 0"),
            ("has_voice", "has_voice INTEGER DEFAULT 0"),
            ("audio_path", "audio_path TEXT"),
            ("audio_url", "audio_url TEXT"),
            ("transcript", "transcript TEXT"),
            ("transcribe_status", "transcribe_status TEXT"),
        ]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            for col_name, ddl in new_columns:
                try:
                    cursor.execute(f"ALTER TABLE tasks ADD COLUMN {ddl}")
                    logger.info(f"Added {col_name} column to tasks table")
                except sqlite3.OperationalError as e:
                    logger.warning(f"Failed to add {col_name} column (it may already exist): {e}")

            # 给缺少 uuid 的现有行回填 uuid，并标记为待推送
            cursor.execute("SELECT task_id FROM tasks WHERE uuid IS NULL OR uuid = ''")
            rows_to_backfill = cursor.fetchall()
            for (task_id,) in rows_to_backfill:
                cursor.execute(
                    "UPDATE tasks SET uuid = ?, dirty = 1 WHERE task_id = ?",
                    (str(uuid.uuid4()), task_id)
                )

            conn.commit()
            logger.info(f"Backfilled uuid for {len(rows_to_backfill)} existing task(s)")
        finally:
            conn.close()
