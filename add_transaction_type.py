"""
Script de migracion para agregar campo transaction_type a transacciones existentes.
Ejecutar una sola vez despues de actualizar models.py
"""
import sqlite3
import os


def migrate_database():
    db_path = 'portfolio.db'

    if not os.path.exists(db_path):
        print("Base de datos no encontrada")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'transaction_type' not in columns:
            print("Agregando columna transaction_type...")
            cursor.execute("""
                ALTER TABLE transactions
                ADD COLUMN transaction_type VARCHAR(10) DEFAULT 'buy'
            """)

            # Actualizar todas las transacciones existentes como compras
            cursor.execute("""
                UPDATE transactions
                SET transaction_type = 'buy'
                WHERE transaction_type IS NULL
            """)

            conn.commit()
            print("Migracion completada exitosamente")
        else:
            print("La columna transaction_type ya existe")

    except Exception as e:
        print(f"Error en migracion: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    migrate_database()
