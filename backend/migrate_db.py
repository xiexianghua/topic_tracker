#!/usr/bin/env python
"""
数据库迁移脚本
从旧的调度方式（interval_minutes和schedule_times）迁移到新的cron表达式
"""

import sqlite3
import json
import os
import sys

def migrate_database(db_path):
    """执行数据库迁移"""
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    # 备份数据库
    backup_path = db_path + '.backup'
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"已创建数据库备份: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查是否已经有cron_expression字段
        cursor.execute("PRAGMA table_info(script)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'cron_expression' not in columns:
            print("添加cron_expression字段...")
            cursor.execute("ALTER TABLE script ADD COLUMN cron_expression TEXT")
            
            # 迁移现有的调度设置
            cursor.execute("SELECT id, interval_minutes, schedule_times, schedule_type FROM script")
            scripts = cursor.fetchall()
            
            for script_id, interval_minutes, schedule_times, schedule_type in scripts:
                cron_expression = ""
                
                if schedule_type == 'interval' and interval_minutes and interval_minutes > 0:
                    # 转换间隔分钟为cron表达式
                    if interval_minutes == 60:
                        cron_expression = "0 * * * *"  # 每小时
                    elif interval_minutes < 60 and 60 % interval_minutes == 0:
                        cron_expression = f"*/{interval_minutes} * * * *"  # 每N分钟
                    else:
                        # 对于其他间隔，使用近似值
                        hours = interval_minutes // 60
                        if hours > 0:
                            cron_expression = f"0 */{hours} * * *"  # 每N小时
                        else:
                            cron_expression = f"*/{interval_minutes} * * * *"
                    
                elif schedule_type == 'fixed_times' and schedule_times:
                    # 转换固定时间为cron表达式
                    try:
                        times = json.loads(schedule_times)
                        if times and len(times) == 1:
                            # 单个时间
                            hour, minute = times[0].split(':')
                            cron_expression = f"{minute} {hour} * * *"
                        elif times:
                            # 多个时间，取第一个，其他的需要手动调整
                            hour, minute = times[0].split(':')
                            cron_expression = f"{minute} {hour} * * *"
                            print(f"脚本ID {script_id} 有多个运行时间: {times}")
                            print(f"  已转换为: {cron_expression} (仅使用第一个时间)")
                            print(f"  其他时间需要手动设置")
                    except:
                        pass
                
                if cron_expression:
                    cursor.execute("UPDATE script SET cron_expression = ? WHERE id = ?", 
                                 (cron_expression, script_id))
                    print(f"脚本ID {script_id}: 已转换为cron表达式 '{cron_expression}'")
        
        # 可选：删除旧字段（建议先运行一段时间确认没问题后再删除）
        # cursor.execute("ALTER TABLE script DROP COLUMN interval_minutes")
        # cursor.execute("ALTER TABLE script DROP COLUMN schedule_times")
        # cursor.execute("ALTER TABLE script DROP COLUMN schedule_type")
        
        conn.commit()
        print("数据库迁移完成！")
        return True
        
    except Exception as e:
        print(f"迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # 获取数据库路径
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # 默认路径
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'scripts.db')
    
    print(f"开始迁移数据库: {db_path}")
    if migrate_database(db_path):
        print("迁移成功！")
    else:
        print("迁移失败！")