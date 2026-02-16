import sqlite3
import csv
import os

# --- 配置参数 ---
DB_NAME = 'deepgloss.db'
CSV_FILE = 'metadata.csv'
# 设定的相对路径前缀 (使用正斜杠以确保跨平台及网页调用的兼容性)
AUDIO_BASE_PATH = "data/audio_cache/audio_segments/"
DEFAULT_DOMAIN_ID = 1


def import_csv_to_db():
    # 1. 检查文件是否存在
    if not os.path.exists(CSV_FILE):
        print(f"❌ 找不到 CSV 文件: {CSV_FILE}")
        return
    if not os.path.exists(DB_NAME):
        print(f"❌ 找不到数据库文件: {DB_NAME}，请确保 schema 已初始化。")
        return

    # 2. 连接数据库
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 统计计数器
    total_processed = 0

    try:
        # 3. 读取 CSV 文件
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # 准备批量插入/更新的数据列表
            records_to_upsert = []

            for row in reader:
                # 提取所需字段 (对应 CSV 的表头)
                transcript_text = row.get('Transcript Text', '').strip()
                hashed_filename = row.get('Hashed Filename', '').strip()

                if not transcript_text:
                    continue  # 跳过空句子

                # 拼接相对路径
                audio_hash = f"{AUDIO_BASE_PATH}{hashed_filename}"

                # 添加到列表 (domain_id, content_en, audio_hash)
                records_to_upsert.append((DEFAULT_DOMAIN_ID, transcript_text, audio_hash))
                total_processed += 1

        # 4. 执行 Upsert 操作 (存在则更新，不存在则插入)
        # 依赖于 schema.sql 中 content_en 的 UNIQUE 约束
        upsert_sql = """
            INSERT INTO sentences (domain_id, content_en, audio_hash)
            VALUES (?, ?, ?)
            ON CONFLICT(content_en) DO UPDATE SET
                audio_hash = excluded.audio_hash;
        """

        cursor.executemany(upsert_sql, records_to_upsert)

        # 5. 提交事务
        conn.commit()
        print(f"✅ 成功处理并导入/更新了 {total_processed} 条句子数据到 deepgloss.db！")

    except sqlite3.Error as e:
        print(f"❌ 数据库操作失败: {e}")
        conn.rollback()
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")
    finally:
        # 6. 关闭连接
        conn.close()


if __name__ == "__main__":
    import_csv_to_db()