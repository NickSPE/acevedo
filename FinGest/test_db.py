from decouple import config
import psycopg2

DEFAULT_KEY = "user123"

try:
    conn = psycopg2.connect(
        dbname=config("DB_NAME", default="fingest_db"),
        user=config("DB_USER", default="user"),
        password=config("DB_PASSWORD", default=DEFAULT_KEY),
        host=config("DB_HOST", default="localhost"),
        port=config("DB_PORT", default="5432"),
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