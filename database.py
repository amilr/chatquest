import psycopg2

# Global variable to hold the database connection
conn = None

def connect_to_db(dbname, user, password, host, port):
    global conn
    try:
        conn = psycopg2.connect(
            dbname = dbname,
            user = user,
            password = password,
            host = host,
            port = port
        )
        print("Connected to the database successfully!")
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        conn = None

def close_db_connection():
    global conn
    if conn:
        conn.close()
        print("Database connection closed.")

def get_game_session(chat_id):
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        chat_id_str = str(chat_id)
        cur.execute("SELECT id FROM game_session WHERE chat_id = %s", (chat_id_str,))
        result = cur.fetchone()
        cur.close()
        return result[0] if result else None
    except psycopg2.Error as e:
        print(f"Error getting game session: {e}")
        return None

def create_game_session(chat_id):
    if not conn:
        return None
    
    try:
        cur = conn.cursor()
        chat_id_str = str(chat_id)
        cur.execute(
            "INSERT INTO game_session (chat_id) VALUES (%s) RETURNING id",
            (chat_id_str,)
        )
        game_session_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return game_session_id
    except psycopg2.Error as e:
        print(f"Error creating game session: {e}")
        return None

def get_message_history(game_session_id):
    if not conn:
        return []
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT sender, message 
            FROM game_message 
            WHERE game_session_id = %s 
            ORDER BY sequence
        """, (game_session_id,))
        messages = cur.fetchall()
        cur.close()
        return [{'sender': msg[0], 'message': msg[1]} for msg in messages]
    except psycopg2.Error as e:
        print(f"Error getting message history: {e}")
        return []

def store_message_to_db(game_session_id, sequence, sender, message):
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO game_message (game_session_id, sequence, sender, message)
            VALUES (%s, %s, %s, %s)
        """, (game_session_id, sequence, sender, message))
        conn.commit()
        cur.close()
        return True
    except psycopg2.Error as e:
        print(f"Error storing message: {e}")
        return False
