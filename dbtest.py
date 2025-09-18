import sqlite3

def add_snmp_community_column():
    # Path to your SQLite database file
    db_path = "C:/Users/hp/Desktop/Portfolio website/IoneTonertrack/backend/printers.db"
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add the 'snmp_community' column to the 'printers' table
        cursor.execute('''
            ALTER TABLE printers ADD COLUMN snmp_community TEXT DEFAULT 'public';
        ''')
        
        # Commit the changes
        conn.commit()
        
        print("Column 'snmp_community' added successfully!")
    
    except sqlite3.OperationalError as e:
        print(f"Error occurred: {e}")
    
    finally:
        # Close the connection
        if conn:
            conn.close()

if __name__ == "__main__":
    add_snmp_community_column()
