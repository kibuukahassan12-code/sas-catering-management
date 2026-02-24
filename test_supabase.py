import psycopg2

try:
    conn = psycopg2.connect(
        "postgresql://postgres:gI3NRd3pZksMKpqp@db.wgatfuaxhiurebltzbog.supabase.co:5432/postgres"
    )
    cur = conn.cursor()
    cur.execute("SELECT NOW();")
    print("Supabase connected successfully! Current time:", cur.fetchone())
    conn.close()
except Exception as e:
    print("Connection failed:", e)
