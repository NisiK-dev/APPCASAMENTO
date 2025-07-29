from app import app, db
from models import *  # Importe todos os seus modelos

def init_database():
    """Inicializa o banco de dados no Supabase"""
    with app.app_context():
        try:
            # Cria todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas com sucesso no Supabase!")

            # Verifica se as tabelas foram criadas
            from sqlalchemy import text
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))

            tables = [row[0] for row in result]
            print(f"📋 Tabelas criadas: {tables}")

        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")

if __name__ == "__main__":
    init_database()