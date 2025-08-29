# ==========================================
# 🎉 SISTEMA RSVP PARA CASAMENTO - ROUTES.PY COMPLETO
# ==========================================
# Arquivo: routes.py
# Descrição: Todas as rotas do sistema RSVP implementadas
# Versão: Completa com todas as funcionalidades administrativas

from flask import render_template, request, jsonify, session, redirect, url_for, flash, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, db
from models import AdminUser as Admin, Guest, GuestGroup, GiftRegistry, VenueInfo
from send_whatsapp import send_bulk_whatsapp_messages, get_wedding_message

import logging
from sqlalchemy import text
from datetime import datetime, date
import os
import uuid
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload

# =========================
# 🔧 Configuração de Locale
# =========================
import locale
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')
except locale.Error:
    logging.warning("Locale 'pt_BR.utf8' não disponível, pode afetar formatação de datas.")

# =========================
# 🔧 Filtros Jinja2
# =========================
@app.template_filter('format_date_br')
def format_date_br(value):
    """Filtro para formatar datas em português brasileiro"""
    meses_map = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
        7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    if not value:
        return ""
    if isinstance(value, date):
        return f"{value.day} de {meses_map.get(value.month, '')} de {value.year}"
    return value

# =========================
# 🌐 ROTAS PÚBLICAS
# =========================

@app.route('/')
def index():
    """Página inicial do sistema"""
    venue = VenueInfo.query.first()
    gifts = GiftRegistry.query.filter_by(is_active=True).order_by(GiftRegistry.id.desc()).limit(3).all()
    return render_template('index.html', venue=venue, gifts=gifts)

@app.route('/rsvp')
def rsvp():
    """Página de confirmação de presença"""
    return render_template('rsvp.html')

@app.route('/search_guest', methods=['POST'])
def search_guest():
    """Buscar convidados via AJAX"""
    name = request.form.get('name', '').strip()
    if not name or len(name) < 3:
        return jsonify({"guests": []})

    # Busca convidados que começam com o nome digitado
    guests = Guest.query.filter(Guest.name.ilike(f"{name}%")).all()

    results = []
    for g in guests:
        results.append({
            "id": g.id,
            "name": g.name,
            "rsvp_status": g.rsvp_status,
            "group_name": g.group.name if g.group else None
        })

    return jsonify({"guests": results})

@app.route('/get_guest_group/')
def get_guest_group(guest_id):
    """Obter grupo de convidados de um convidado específico"""
    guest = Guest.query.get_or_404(guest_id)

    if guest.group_id:
        group = GuestGroup.query.get(guest.group_id)
        guests = group.guests if group else [guest]
    else:
        guests = [guest]

    guests_data = [
        {"id": g.id, "name": g.name, "rsvp_status": g.rsvp_status}
        for g in guests
    ]

    return jsonify({
        "selected_guest_name": guest.name,
        "guests": guests_data
    })

@app.route('/confirm_rsvp', methods=['POST'])
def confirm_rsvp():
    """Processar confirmação de presença"""
    guest_ids = request.form.getlist('guest_ids')
    if not guest_ids:
        flash("Nenhum convidado selecionado.", "danger")
        return redirect(url_for('rsvp'))

    confirmed_count = 0
    for guest_id in guest_ids:
        guest = Guest.query.get(int(guest_id))
        if guest:
            status = request.form.get(f"rsvp_{guest.id}")
            if status in ['confirmado', 'nao_confirmado']:
                guest.rsvp_status = status
                db.session.add(guest)
                confirmed_count += 1

    db.session.commit()
    
    if confirmed_count > 0:
        flash(f"Confirmação registrada para {confirmed_count} convidado(s)!", "success")
    else:
        flash("Nenhuma confirmação foi processada.", "warning")
    
    return redirect(url_for('rsvp'))

@app.route('/gifts')
def gifts():
    """Página de lista de presentes"""
    gifts = GiftRegistry.query.filter_by(is_active=True).all()
    return render_template('gifts.html', gifts=gifts)

@app.route('/api/event-datetime')
def api_event_datetime():
    """API para obter data e hora do evento"""
    venue = VenueInfo.query.first()
    if venue and venue.event_datetime:
        return jsonify({"datetime": venue.event_datetime.isoformat(), "success": True})
    return jsonify({"datetime": "2025-10-19T18:30:00", "success": True})

@app.route('/agradecimento')
def agradecimento():
    """Página de agradecimento pelo presente"""
    return render_template('agradecimento.html')

@app.route('/agradecimento/')
def agradecimento_personalizado(guest_id):
    """Página de agradecimento personalizada"""
    guest = Guest.query.get_or_404(guest_id)
    return render_template('agradecimento.html', guest_name=guest.name)

# =========================
# 🔐 ROTAS DE AUTENTICAÇÃO ADMIN
# =========================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login do administrador"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        flash('Usuário ou senha inválidos!', 'danger')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Logout do administrador"""
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('index'))

def admin_required():
    """Decorator para verificar autenticação admin"""
    if 'admin_id' not in session:
        flash('Acesso negado! Faça login como administrador.', 'danger')
        return redirect(url_for('admin_login'))
    return None

# =========================
# 🏠 DASHBOARD ADMINISTRATIVO
# =========================

@app.route('/admin/dashboard')
def admin_dashboard():
    """Dashboard principal do administrador"""
    auth_check = admin_required()
    if auth_check:
        return auth_check

    # Estatísticas dos convidados
    total_guests = Guest.query.count()
    confirmed = Guest.query.filter_by(rsvp_status='confirmado').count()
    pending = Guest.query.filter_by(rsvp_status='pendente').count()
    declined = Guest.query.filter_by(rsvp_status='nao_confirmado').count()

    return render_template(
        'admin_dashboard.html',
        total_guests=total_guests,
        confirmed_guests=confirmed,
        pending_guests=pending,
        declined_guests=declined,
        total_groups=GuestGroup.query.count(),
        total_gifts=GiftRegistry.query.filter_by(is_active=True).count()
    )

# =========================
# 👥 GERENCIAMENTO DE CONVIDADOS
# =========================

@app.route('/admin/guests')
def admin_guests():
    """Página de gerenciamento de convidados"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    guests = Guest.query.options(joinedload(Guest.group)).all()
    groups = GuestGroup.query.all()
    
    return render_template('admin_guests.html', guests=guests, groups=groups)

@app.route('/admin/add_guest', methods=['POST'])
def add_guest():
    """Adicionar novo convidado"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    try:
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        group_id = request.form.get('group_id')
        
        if not name:
            flash("Nome do convidado é obrigatório!", "danger")
            return redirect(url_for('admin_guests'))
        
        # Verificar se já existe
        existing = Guest.query.filter_by(name=name).first()
        if existing:
            flash(f"Convidado '{name}' já existe!", "warning")
            return redirect(url_for('admin_guests'))
        
        new_guest = Guest(
            name=name,
            phone=phone if phone else None,
            group_id=int(group_id) if group_id and group_id.isdigit() else None,
            rsvp_status='pendente'
        )
        
        db.session.add(new_guest)
        db.session.commit()
        flash(f"Convidado '{name}' adicionado com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao adicionar convidado: {str(e)}", "danger")
    
    return redirect(url_for('admin_guests'))

@app.route('/admin/edit_guest/', methods=['POST'])
def edit_guest(guest_id):
    """Editar convidado existente"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    try:
        guest = Guest.query.get_or_404(guest_id)
        
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        group_id = request.form.get('group_id')
        rsvp_status = request.form.get('rsvp_status', 'pendente')
        
        if not name:
            flash("Nome do convidado é obrigatório!", "danger")
            return redirect(url_for('admin_guests'))
        
        guest.name = name
        guest.phone = phone if phone else None
        guest.group_id = int(group_id) if group_id and group_id.isdigit() else None
        guest.rsvp_status = rsvp_status
        
        db.session.commit()
        flash(f"Convidado '{name}' atualizado com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao editar convidado: {str(e)}", "danger")
    
    return redirect(url_for('admin_guests'))

@app.route('/admin/delete_guest/', methods=['POST'])
def delete_guest(guest_id):
    """Deletar convidado"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    try:
        guest = Guest.query.get_or_404(guest_id)
        guest_name = guest.name
        
        db.session.delete(guest)
        db.session.commit()
        flash(f"Convidado '{guest_name}' removido com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover convidado: {str(e)}", "danger")
    
    return redirect(url_for('admin_guests'))

# =========================
# 👨‍👩‍👧‍👦 GERENCIAMENTO DE GRUPOS
# =========================

@app.route('/admin/groups')
def admin_groups():
    """Página de gerenciamento de grupos"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    groups = GuestGroup.query.all()
    return render_template('admin_groups.html', groups=groups)

@app.route('/admin/add_group', methods=['POST'])
def add_group():
    """Adicionar novo grupo"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash("Nome do grupo é obrigatório!", "danger")
            return redirect(url_for('admin_groups'))
        
        # Verificar se já existe
        existing = GuestGroup.query.filter_by(name=name).first()
        if existing:
            flash(f"Grupo '{name}' já existe!", "warning")
            return redirect(url_for('admin_groups'))
        
        new_group = GuestGroup(
            name=name,
            description=description if description else None
        )
        
        db.session.add(new_group)
        db.session.commit()
        flash(f"Grupo '{name}' criado com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao criar grupo: {str(e)}", "danger")
    
    return redirect(url_for('admin_groups'))

@app.route('/admin/edit_group/', methods=['POST'])
def edit_group(group_id):
    """Editar grupo existente"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    try:
        group = GuestGroup.query.get_or_404(group_id)
        
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash("Nome do grupo é obrigatório!", "danger")
            return redirect(url_for('admin_groups'))
        
        group.name = name
        group.description = description if description else None
        
        db.session.commit()
        flash(f"Grupo '{name}' atualizado com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao editar grupo: {str(e)}", "danger")
    
    return redirect(url_for('admin_groups'))

@app.route('/admin/delete_group/', methods=['POST'])
def delete_group(group_id):
    """Deletar grupo"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    try:
        group = GuestGroup.query.get_or_404(group_id)
        group_name = group.name
        
        # Verificar se há convidados no grupo
        guests_in_group = Guest.query.filter_by(group_id=group_id).count()
        if guests_in_group > 0:
            flash(f"Não é possível deletar o grupo '{group_name}' pois há {guests_in_group} convidado(s) associado(s)!", "danger")
            return redirect(url_for('admin_groups'))
        
        db.session.delete(group)
        db.session.commit()
        flash(f"Grupo '{group_name}' removido com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover grupo: {str(e)}", "danger")
    
    return redirect(url_for('admin_groups'))

# =========================
# 🎁 GERENCIAMENTO DE PRESENTES
# =========================

@app.route('/admin/gifts')
def admin_gifts():
    """Página de gerenciamento de presentes"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    gifts = GiftRegistry.query.all()
    return render_template('admin_gifts.html', gifts=gifts)

@app.route('/admin/add_gift', methods=['POST'])
def add_gift():
    """Adicionar novo presente"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    try:
        item_name = request.form.get('item_name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '').strip()
        image_url = request.form.get('image_url', '').strip()
        pix_key = request.form.get('pix_key', '').strip()
        pix_link = request.form.get('pix_link', '').strip()
        credit_card_link = request.form.get('credit_card_link', '').strip()
        
        if not item_name:
            flash("Nome do presente é obrigatório!", "danger")
            return redirect(url_for('admin_gifts'))
        
        new_gift = GiftRegistry(
            item_name=item_name,
            description=description if description else None,
            price=price if price else None,
            image_url=image_url if image_url else None,
            pix_key=pix_key if pix_key else None,
            pix_link=pix_link if pix_link else None,
            credit_card_link=credit_card_link if credit_card_link else None,
            is_active=True
        )
        
        db.session.add(new_gift)
        db.session.commit()
        flash(f"Presente '{item_name}' adicionado com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao adicionar presente: {str(e)}", "danger")
    
    return redirect(url_for('admin_gifts'))

@app.route('/admin/edit_gift/', methods=['POST'])
def edit_gift(gift_id):
    """Editar presente existente"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    try:
        gift = GiftRegistry.query.get_or_404(gift_id)
        
        gift.item_name = request.form.get('item_name', '').strip()
        gift.description = request.form.get('description', '').strip()
        gift.price = request.form.get('price', '').strip()
        gift.image_url = request.form.get('image_url', '').strip()
        gift.pix_key = request.form.get('pix_key', '').strip()
        gift.pix_link = request.form.get('pix_link', '').strip()
        gift.credit_card_link = request.form.get('credit_card_link', '').strip()
        gift.is_active = 'is_active' in request.form
        
        if not gift.item_name:
            flash("Nome do presente é obrigatório!", "danger")
            return redirect(url_for('admin_gifts'))
        
        db.session.commit()
        flash(f"Presente '{gift.item_name}' atualizado com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao editar presente: {str(e)}", "danger")
    
    return redirect(url_for('admin_gifts'))

@app.route('/admin/delete_gift/', methods=['POST'])
def delete_gift(gift_id):
    """Deletar presente"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    try:
        gift = GiftRegistry.query.get_or_404(gift_id)
        gift_name = gift.item_name
        
        db.session.delete(gift)
        db.session.commit()
        flash(f"Presente '{gift_name}' removido com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover presente: {str(e)}", "danger")
    
    return redirect(url_for('admin_gifts'))

# =========================
# 🏰 GERENCIAMENTO DO LOCAL DO EVENTO
# =========================

@app.route('/admin/venue')
def admin_venue():
    """Página de gerenciamento do local do evento"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    venue = VenueInfo.query.first()
    return render_template('admin_venue.html', venue=venue)

@app.route('/admin/update_venue', methods=['POST'])
def update_venue():
    """Atualizar informações do local do evento"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    try:
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        map_link = request.form.get('map_link', '').strip()
        description = request.form.get('description', '').strip()
        event_date = request.form.get('event_date', '').strip()
        event_time = request.form.get('event_time', '').strip()
        
        if not name:
            flash("Nome do local é obrigatório!", "danger")
            return redirect(url_for('admin_venue'))
        
        # Buscar ou criar venue
        venue = VenueInfo.query.first()
        if not venue:
            venue = VenueInfo()
        
        venue.name = name
        venue.address = address if address else None
        venue.map_link = map_link if map_link else None
        venue.description = description if description else None
        
        # Processar data e hora
        if event_date and event_time:
            try:
                event_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
                venue.event_datetime = event_datetime
                venue.date = event_datetime.date()
                venue.time = event_datetime.time()
            except ValueError:
                flash("Formato de data ou hora inválido!", "warning")
        elif event_date:
            try:
                event_date_obj = datetime.strptime(event_date, "%Y-%m-%d").date()
                venue.date = event_date_obj
            except ValueError:
                flash("Formato de data inválido!", "warning")
        
        venue.updated_at = datetime.utcnow()
        
        if not venue.id:
            db.session.add(venue)
        
        db.session.commit()
        flash("Informações do local atualizadas com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao atualizar informações do local: {str(e)}", "danger")
    
    return redirect(url_for('admin_venue'))

# =========================
# 📱 GERENCIAMENTO DE WHATSAPP
# =========================

@app.route('/admin/whatsapp')
def admin_whatsapp():
    """Página de gerenciamento do WhatsApp"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    # Convidados com telefone cadastrado
    guests_with_phone = Guest.query.filter(Guest.phone.isnot(None), Guest.phone != '').all()
    venue = VenueInfo.query.first()
    
    return render_template('admin_whatsapp.html', 
                         guests=guests_with_phone, 
                         venue=venue,
                         total_with_phone=len(guests_with_phone))

@app.route('/admin/send_whatsapp', methods=['POST'])
def send_whatsapp():
    """Enviar mensagens WhatsApp em lote"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    try:
        message_type = request.form.get('message_type', 'invite')
        custom_message = request.form.get('custom_message', '').strip()
        selected_guests = request.form.getlist('guest_ids')
        
        if not selected_guests:
            flash("Nenhum convidado selecionado!", "warning")
            return redirect(url_for('admin_whatsapp'))
        
        # Obter convidados selecionados
        guests = Guest.query.filter(Guest.id.in_([int(id) for id in selected_guests])).all()
        
        # Verificar se todos têm telefone
        guests_without_phone = [g for g in guests if not g.phone]
        if guests_without_phone:
            names = [g.name for g in guests_without_phone]
            flash(f"Os seguintes convidados não têm telefone cadastrado: {', '.join(names)}", "warning")
        
        guests_with_phone = [g for g in guests if g.phone]
        
        if not guests_with_phone:
            flash("Nenhum convidado selecionado possui telefone cadastrado!", "danger")
            return redirect(url_for('admin_whatsapp'))
        
        # Preparar mensagem
        if message_type == 'custom' and custom_message:
            message = custom_message
        else:
            venue = VenueInfo.query.first()
            message = get_wedding_message(message_type, venue)
        
        # Enviar mensagens
        success_count, error_count, errors = send_bulk_whatsapp_messages(guests_with_phone, message)
        
        if success_count > 0:
            flash(f"✅ {success_count} mensagem(s) enviada(s) com sucesso!", "success")
        
        if error_count > 0:
            flash(f"⚠️ {error_count} erro(s) ao enviar mensagens. Verifique os logs.", "warning")
            for error in errors[:3]:  # Mostrar apenas os 3 primeiros erros
                flash(f"Erro: {error}", "danger")
        
    except Exception as e:
        flash(f"Erro geral no envio: {str(e)}", "danger")
        logging.error(f"Erro no envio de WhatsApp: {e}")
    
    return redirect(url_for('admin_whatsapp'))

# =========================
# ⚙️ CONFIGURAÇÕES DO SISTEMA
# =========================

@app.route('/admin/settings')
def admin_settings():
    """Página de configurações do administrador"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    admin = Admin.query.get(session['admin_id'])
    return render_template('admin_settings.html', admin=admin)

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    """Alterar senha do administrador"""
    auth_check = admin_required()
    if auth_check:
        return auth_check
    
    try:
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        admin = Admin.query.get(session['admin_id'])
        
        # Verificar senha atual
        if not check_password_hash(admin.password_hash, current_password):
            flash("Senha atual incorreta!", "danger")
            return redirect(url_for('admin_settings'))
        
        # Validar nova senha
        if len(new_password) < 6:
            flash("A nova senha deve ter pelo menos 6 caracteres!", "danger")
            return redirect(url_for('admin_settings'))
        
        if new_password != confirm_password:
            flash("A confirmação de senha não confere!", "danger")
            return redirect(url_for('admin_settings'))
        
        # Atualizar senha
        admin.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash("Senha alterada com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao alterar senha: {str(e)}", "danger")
    
    return redirect(url_for('admin_settings'))

# =========================
# 🔧 MIDDLEWARE E UTILITÁRIOS
# =========================

@app.before_request
def create_admin():
    """Criar usuário admin padrão se não existir"""
    if not Admin.query.first():
        admin = Admin(
            username='admin', 
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro ao criar admin padrão: {e}")

# =========================
# 🚨 TRATAMENTO DE ERROS
# =========================

@app.errorhandler(404)
def not_found(e):
    """Página não encontrada"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Erro interno do servidor"""
    db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden(e):
    """Acesso proibido"""
    return render_template('403.html'), 403

# =========================
# 🏥 HEALTH CHECK
# =========================

@app.route('/healthz')
def healthz():
    """Verificação de saúde do sistema"""
    try:
        # Testar conexão com banco
        db.session.execute(text("SELECT 1")).scalar()
        
        # Estatísticas básicas
        stats = {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "guests": Guest.query.count(),
            "groups": GuestGroup.query.count(),
            "gifts": GiftRegistry.query.count()
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

# =========================
# 📊 API ENDPOINTS EXTRAS
# =========================

@app.route('/api/stats')
def api_stats():
    """API para estatísticas do sistema"""
    auth_check = admin_required()
    if auth_check:
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        stats = {
            "total_guests": Guest.query.count(),
            "confirmed": Guest.query.filter_by(rsvp_status='confirmado').count(),
            "pending": Guest.query.filter_by(rsvp_status='pendente').count(),
            "declined": Guest.query.filter_by(rsvp_status='nao_confirmado').count(),
            "total_groups": GuestGroup.query.count(),
            "total_gifts": GiftRegistry.query.filter_by(is_active=True).count(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================
# 🎯 FIM DO ARQUIVO ROUTES.PY
# =========================

# 📝 NOTAS IMPORTANTES:
# 1. Certifique-se de que todos os templates estão na pasta /templates/
# 2. Verifique se o arquivo send_whatsapp.py existe e tem as funções necessárias
# 3. Configure as variáveis de ambiente (DATABASE_URL, SESSION_SECRET, etc.)
# 4. Execute 'flask db upgrade' se usando migrações
# 5. Teste cada funcionalidade após implementar
