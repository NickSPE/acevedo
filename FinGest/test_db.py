import psycopg2

try:
    conn = psycopg2.connect(
        dbname="fingest_db",
        user="user",
        password="user123",
        host="localhost",
        port="5432",
        connect_timeout=3
    )
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    print("✅ Conexión exitosa! PostgreSQL está funcionando correctamente")
    conn.close()
except Exception as e:
    print(f"❌ Error de conexión: {str(e)}")
    print("Posibles soluciones:")
    print("1. Verifica que PostgreSQL esté corriendo")
    print("2. Revisa el usuario y contraseña")
    print("3. Prueba con contraseñas más simples (sin caracteres especiales)")