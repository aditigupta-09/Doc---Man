#!/usr/bin/env python
import psycopg2
import psycopg2.extras
import time
import os

DB_HOST = "localhost"
DB_PORT = 4321
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_NAME = "omnidocs"

OUTPUT_FILE = "database_records.txt"

def format_table(title, headers, rows):
    out = []
    out.append(f"\n=== {title.upper()} ===")
    if not rows:
        out.append("No records found.")
        return "\n".join(out) + "\n"
        
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, val in enumerate(row):
            widths[idx] = max(widths[idx], len(str(val if val is not None else "")))
            
    # Print header
    header_str = " | ".join(f"{str(headers[i]).ljust(widths[i])}" for i in range(len(headers)))
    out.append(header_str)
    out.append("-" * len(header_str))
    
    # Print rows
    for row in rows:
        out.append(" | ".join(f"{str(row[i] if row[i] is not None else '').ljust(widths[i])}" for i in range(len(headers))))
    return "\n".join(out) + "\n"

def main():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME
        )
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        file_content = []
        file_content.append("+" + "="*70 + "+")
        file_content.append(f"| Active Database: PostgreSQL on port {DB_PORT} ".ljust(71) + "|")
        file_content.append(f"| Database Name:   {DB_NAME} ".ljust(71) + "|")
        file_content.append(f"| Last Updated:    {time.strftime('%Y-%m-%d %H:%M:%S')} ".ljust(71) + "|")
        file_content.append("+" + "="*70 + "+")
        
        # 1. Users
        cursor.execute("SELECT id, email, role FROM users ORDER BY id")
        rows = cursor.fetchall()
        file_content.append(format_table("Users Index", ["ID", "Email Address", "System Role"], [[r[0], r[1], r[2]] for r in rows]))
        
        # 2. Documents
        cursor.execute("SELECT id, name, category, uploaded_by, version, file_size FROM documents ORDER BY id")
        rows = cursor.fetchall()
        file_content.append(format_table("Documents Index", ["ID", "Filename", "Category", "Uploaded By", "Version", "Size (bytes)"], [[r[0], r[1], r[2], r[3], r[4], r[5]] for r in rows]))
        
        # 3. Pending & Approved Permissions
        cursor.execute("""
            SELECT p.id, d.name, p.user_email, p.status, p.purpose 
            FROM document_permissions p
            JOIN documents d ON p.document_id = d.id
            ORDER BY p.id
        """)
        rows = cursor.fetchall()
        file_content.append(format_table("Document Access Requests", ["ID", "Document Name", "Requester Email", "Status", "Purpose"], [[r[0], r[1], r[2], r[3], r[4]] for r in rows]))
        
        # 4. Password Reset Requests
        cursor.execute("SELECT id, email, status, temp_password FROM password_reset_requests ORDER BY id")
        rows = cursor.fetchall()
        file_content.append(format_table("Password Reset Requests", ["ID", "User Email", "Status", "Temporary Password"], [[r[0], r[1], r[2], r[3]] for r in rows]))
        
        # 5. Audit Logs
        cursor.execute("SELECT id, username, action, details, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT 30")
        rows = cursor.fetchall()
        log_rows = []
        for r in rows:
            t_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(r[4]))
            log_rows.append([r[0], t_str, r[1], r[2], r[3]])
        file_content.append(format_table("Recent System Audit Logs (Last 30)", ["ID", "Timestamp", "User", "Action", "Details"], log_rows))
        
        conn.close()
        
        # Write to file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(file_content))
            
        print(f"\n[OK] Database records written to file successfully: {os.path.abspath(OUTPUT_FILE)}")
    except Exception as e:
        print("\n[!] Connection Error: Could not connect to PostgreSQL database.")
        print(f"Details: {e}")

if __name__ == "__main__":
    main()
