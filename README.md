# Sistema RSVP para Casamento 💒

Um sistema web completo e elegante para gerenciamento de confirmações de presença (RSVP) em casamentos, desenvolvido com Flask e PostgreSQL.

## 🚀 Funcionalidades

### Para Convidados
- **Busca Inteligente**: Encontre seu nome e confirme presença facilmente
- **Confirmação em Grupo**: Confirme presença para toda a família de uma só vez
- **Lista de Presentes**: Visualize a lista de presentes com links para lojas
- **Interface Responsiva**: Funciona perfeitamente em celulares e computadores

### Para Administradores
- **Painel Completo**: Dashboard com estatísticas e controle total
- **Gestão de Convidados**: Adicione, edite e organize convidados em grupos/famílias
- **Gestão de Grupos**: Organize convidados por famílias ou categorias
- **Informações do Local**: Configure detalhes do evento, endereço e mapas
- **Lista de Presentes**: Gerencie presentes com preços e links para lojas
- **Envio de WhatsApp**: Integração com Twilio para envio de convites e lembretes

## 📋 Pré-requisitos

- Python 3.11+
- PostgreSQL
- Conta Twilio (opcional, para WhatsApp)

## 🛠️ Configuração Local

### 1. Clone o Repositório
```bash
git clone <seu-repositorio>
cd sistema-rsvp-casamento
```

### 2. Instale as Dependências
```bash
pip install -r requirements.txt
```

### 3. Configure Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto:

```env
# Configuração do Banco de Dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/wedding_rsvp

# Chave Secreta da Aplicação
SESSION_SECRET=sua-chave-secreta-super-segura

# Configuração Twilio (Opcional)
TWILIO_ACCOUNT_SID=seu_account_sid
TWILIO_AUTH_TOKEN=seu_auth_token
TWILIO_PHONE_NUMBER=+5511999999999
```

### 4. Configure o Banco de Dados PostgreSQL

#### Instale o PostgreSQL:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql
```

#### Crie o banco de dados:
```bash
sudo -u postgres psql
CREATE DATABASE wedding_rsvp;
CREATE USER wedding_user WITH PASSWORD 'sua_senha';
GRANT ALL PRIVILEGES ON DATABASE wedding_rsvp TO wedding_user;
\q
```

### 5. Execute a Aplicação
```bash
python main.py
```

A aplicação estará disponível em `http://localhost:5000`

## 🌐 Hospedagem no Replit

### Configuração Rápida

1. **Fork o Projeto**: Importe este projeto no Replit
2. **Configure as Variáveis**: No painel de Secrets do Replit, adicione:
   - `SESSION_SECRET`: Uma chave secreta única
   - `TWILIO_ACCOUNT_SID`: (opcional) Seu SID da Twilio
   - `TWILIO_AUTH_TOKEN`: (opcional) Seu token da Twilio
   - `TWILIO_PHONE_NUMBER`: (opcional) Seu número do WhatsApp Business

3. **Execute**: Clique em "Run" - o PostgreSQL será configurado automaticamente

### Deploy em Produção

O projeto está pronto para deploy no Replit Deployments:

1. Clique no botão "Deploy" no Replit
2. Configure seu domínio personalizado (opcional)
3. O sistema será hospedado automaticamente com HTTPS e certificados SSL

## 📊 Estrutura do Banco de Dados

### Tabelas Principais

#### `admin`
- Armazena credenciais dos administradores
- Senhas criptografadas com Werkzeug

#### `guest_group`
- Organiza convidados em famílias ou grupos
- Permite confirmação em lote

#### `guest`
- Informações dos convidados
- Status de confirmação (pendente, confirmado, não confirmado)
- Números de telefone para WhatsApp

#### `venue_info`
- Detalhes do local do evento
- Data, hora e links do Google Maps

#### `gift_registry`
- Lista de presentes
- Preços e links para lojas

## 🔐 Acesso Administrativo

### Credenciais Padrão
- **Usuário**: `admin`
- **Senha**: `admin123`

**⚠️ IMPORTANTE**: Altere estas credenciais após a primeira configuração!

### Alterando a Senha do Admin
1. Acesse `/admin/login`
2. Faça login com as credenciais padrão
3. No dashboard, vá em "Configurações" para alterar a senha

## 📱 Configuração do WhatsApp (Twilio)

### 1. Criar Conta Twilio
1. Acesse [twilio.com](https://www.twilio.com)
2. Crie uma conta gratuita
3. Verifique seu número de telefone

### 2. Configurar WhatsApp Business
1. No Console Twilio, vá em "Messaging" > "Try it out" > "Send a WhatsApp message"
2. Siga as instruções para configurar o WhatsApp Business
3. Anote suas credenciais (Account SID, Auth Token, Phone Number)

### 3. Adicionar Credenciais
No Replit, vá em "Secrets" e adicione:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`

## 🎨 Personalização

### Cores e Tema
Edite o arquivo `static/style.css` para personalizar:
- Cores do tema
- Fontes
- Espaçamentos
- Animações

### Templates
Os templates estão em `templates/`:
- `base.html`: Layout base
- `index.html`: Página inicial
- `rsvp.html`: Formulário de confirmação
- `gifts.html`: Lista de presentes
- `admin_*.html`: Painéis administrativos

### Mensagens do WhatsApp
Edite `send_whatsapp.py` para personalizar as mensagens automáticas.

## 🚀 Funcionalidades Avançadas

### Busca Inteligente de Convidados
- API REST para busca em tempo real
- Exibição automática de famílias/grupos
- Confirmação individual ou em lote

### Sincronização de Grupos
- Quando um membro da família confirma, o sistema sugere confirmar todos
- Gestão automática de relacionamentos familiares

### Dashboard com Estatísticas
- Total de convidados confirmados
- Porcentagem de confirmações
- Grupos com mais/menos confirmações

## 🔧 Solução de Problemas

### Erro de Banco de Dados
```
RuntimeError: Either 'SQLALCHEMY_DATABASE_URI' or 'SQLALCHEMY_BINDS' must be set.
```
**Solução**: Verifique se a variável `DATABASE_URL` está configurada corretamente.

### Erro de Sessão
```
RuntimeError: The session is unavailable because no secret key was set.
```
**Solução**: Configure a variável `SESSION_SECRET` com uma chave única.

### WhatsApp não Funciona
1. Verifique se as credenciais Twilio estão corretas
2. Confirme se o número está no formato internacional (+5511999999999)
3. Verifique se sua conta Twilio tem créditos

## 📞 Suporte

Para suporte técnico ou dúvidas:
1. Verifique a seção de solução de problemas
2. Consulte a documentação do Flask: [flask.palletsprojects.com](https://flask.palletsprojects.com)
3. Documentação do Twilio: [twilio.com/docs](https://www.twilio.com/docs)

## 🎉 Dicas para o Dia do Casamento

### Antes do Evento
1. Exporte a lista de convidados confirmados
2. Envie lembretes via WhatsApp 1-2 dias antes
3. Prepare um QR Code com o link do RSVP para convidados de última hora

### Durante o Evento
1. Use a lista exportada para controle de entrada
2. O sistema pode ser usado em tablets para check-in em tempo real

## 📄 Licença

Este projeto é de código aberto. Sinta-se livre para usar, modificar e distribuir.

---

**Desenvolvido com ❤️ para tornar seu casamento ainda mais especial!**