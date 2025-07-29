from app import app, db
import os

def init_database():
    """Inicializa o banco de dados no Supabase"""
    print("🔄 Iniciando migração do banco...")
    print(f"🌐 DATABASE_URL configurada: {'Sim' if os.environ.get('DATABASE_URL') else 'Não'}")
    
    with app.app_context():
        try:
            # Testa a conexão primeiro
            db.engine.execute('SELECT 1')
            print("✅ Conexão com banco OK!")
            
            # Cria todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas com sucesso no Supabase!")
            
            # Lista as tabelas criadas
            from sqlalchemy import text
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name NOT LIKE '%pgsodium%'
                AND table_name NOT LIKE '%vault%'
            """))
            
            tables = [row[0] for row in result]
            print(f"📋 Tabelas encontradas: {tables}")
            
        except Exception as e:
            print(f"❌ Erro detalhado: {e}")
            print(f"🔍 Tipo do erro: {type(e).__name__}")
            
if __name__ == "__main__":
    init_database()
