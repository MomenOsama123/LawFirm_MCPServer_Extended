import sqlite3

def create_job(conn, job_id, triggered_by, total_items):
    conn.execute("""
        INSERT INTO batch_job
        (job_id, triggered_by, job_type, total_items, processed_items, status, started_at)
        VALUES (?, ?, 'bulk_conflict_check', ?, 0, 'running', datetime('now'))
    """, (job_id, triggered_by, total_items))
    conn.commit()

def update_progress(conn, job_id):
    conn.execute("""
        UPDATE batch_job
        SET processed_items = processed_items + 1
        WHERE job_id = ?
    """, (job_id,))
    conn.commit()

def get_progress(conn, job_id):
    cursor = conn.execute("""
        SELECT processed_items, total_items, status
        FROM batch_job
        WHERE job_id = ?
    """, (job_id,))

    return cursor.fetchone()


def complete_job(conn, job_id):
    conn.execute("""
        UPDATE batch_job
        SET status = 'completed',
            completed_at = datetime('now')
        WHERE job_id = ?
    """, (job_id,))
    conn.commit()

def fail_job(conn, job_id):
    conn.execute("""
        UPDATE batch_job
        SET status = 'failed',
            completed_at = datetime('now')
        WHERE job_id = ?
    """, (job_id,))
    conn.commit()
