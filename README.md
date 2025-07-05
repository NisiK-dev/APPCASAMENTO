# Sistema RSVP para Casamento - Versão Completa

Um sistema web avançado para confirmação de presença em casamentos, desenvolvido com Flask e PostgreSQL, com recursos inteligentes de sincronização de grupos e gerenciamento completo de eventos.

## Funcionalidades Principais

### 🎯 Para Convidados
- **Busca Inteligente**: Sistema de busca por nome com sincronização automática de grupos familiares
- **Confirmação em Grupo**: Permite confirmar presença para múltiplos convidados de uma vez (família/acompanhantes)
- **Lista de Presentes**: Visualização da lista de presentes com links para lojas
- **Informações do Local**: Endereço completo, data, horário e mapa interativo
- **Interface Responsiva**: Funciona perfeitamente em dispositivos móveis e desktop

### 🛠️ Para Administradores
- **Dashboard Completo**: Estatísticas em tempo real e visão geral do evento
- **Gerenciamento de Grupos**: Criação e organização de grupos de convidados (famílias, amigos, etc.)
- **Lista de Convidados Avançada**: Adição de telefone, agrupamento e status individual
- **Gerenciamento do Local**: Configuração completa das informações do evento
- **Lista de Presentes**: Administração da lista com preços, links e status
- **Acesso Discreto**: Login administrativo não-intrusivo na interface pública

### 🔒 Segurança e Performance
- Autenticação segura com hash de senhas
- Proteção contra injeção SQL
- Validação robusta de dados
- Interface responsiva com Bootstrap 5
- Banco de dados PostgreSQL para escalabilidade

## Arquitetura do Sistema

### Backend
- **Framework**: Flask (Python 3.11)
- **Banco de Dados**: PostgreSQL com SQLAlchemy ORM
- **Autenticação**: Session-based com Werkzeug
- **API**: Endpoints RESTful para busca dinâmica

### Frontend
- **Templates**: Jinja2 com layout responsivo
- **CSS Framework**: Bootstrap 5 com tema escuro
- **JavaScript**: Vanilla JS para interatividade
- **Ícones**: Font Awesome 6.0

### Estrutura do Banco de Dados
- **Admin**: Credenciais do administrador
- **GuestGroup**: Grupos de convidados (famílias, etc.)
- **Guest**: Convidados com telefone e vinculação a grupos
- **VenueInfo**: Informações completas do local
- **GiftRegistry**: Lista de presentes com status e links

## Instalação e Configuração

### 1. Pré-requisitos
- Python 3.11+
- PostgreSQL
- Replit (ambiente recomendado)

### 2. Configuração do Ambiente
```bash
# O sistema é configurado automaticamente no Replit
# As dependências são instaladas via pyproject.toml
