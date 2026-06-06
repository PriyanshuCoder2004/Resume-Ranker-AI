import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

def inspect_database():
    if not os.path.exists(DATABASE):
        print(f"Error: Database file not found at {DATABASE}. Start the server and register a user first.")
        return
        
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check tables list
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        print(f"Tables present in database: {tables}\n")
        
        if 'users' in tables:
            cursor.execute("SELECT id, username, email, created_at FROM users")
            users = cursor.fetchall()
            print(f"=== REGISTERED USERS ({len(users)}) ===")
            for user in users:
                print(f"ID: {user['id']} | Username: {user['username']} | Email: {user['email']} | Joined: {user['created_at']}")
        else:
            print("Table 'users' does not exist yet.")
            
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    inspect_database()
