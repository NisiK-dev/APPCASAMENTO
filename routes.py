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
# 🔧 Rotas Públicas
# =========================
@app.route('/')
def index():
    venue = VenueInfo.query.first()
    gifts = GiftRegistry.query.filter_by(is_active=True).order_by(GiftRegistry.id.desc()).limit(3).all()
    return render_template('index.html', venue=venue, gifts=gifts)

@app.route('/rsvp')
def rsvp():
    """Página de confirmação de presença"""
    return render_template('rsvp.html')

# Buscar convidados manualmente via botão
@app.route('/search_guest', methods=['POST'])
def search_guest():
    name = request.form.get('name', '').strip()
    if not name or len(name) < 3:
        return jsonify({"guests": []})

    # 🔧 Só busca quem COMEÇA com o nome digitado
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

@app.route('/get_guest_group/<int:guest_id>')
def get_guest_group(guest_id):
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
    guest_ids = request.form.getlist('guest_ids')
    if not guest_ids:
        flash("Nenhum convidado selecionado.", "danger")
        return redirect(url_for('rsvp'))

    for guest_id in guest_ids:
        guest = Guest.query.get(int(guest_id))
        if guest:
            status = request.form.get(f"rsvp_{guest.id}")
            if status in ['confirmado', 'nao_confirmado']:
                guest.rsvp_status = status
                db.session.add(guest)

    db.session.commit()
    flash("Confirmação registrada com sucesso!", "success")
    return redirect(url_for('rsvp'))

@app.route('/gifts')
def gifts():
    gifts = GiftRegistry.query.filter_by(is_active=True).all()
    return render_template('gifts.html', gifts=gifts)

@app.route('/api/event-datetime')
def api_event_datetime():
    venue = VenueInfo.query.first()
    if venue and venue.event_datetime:
        return jsonify({"datetime": venue.event_datetime.isoformat(), "success": True})
    return jsonify({"datetime": "2025-10-19T18:30:00", "success": True})

# =========================
# 🔧 Rotas Admin
# =========================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
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
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))

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
        total_gifts=GiftRegistry.query.count()
    )

@app.route('/admin/guests')
def admin_guests():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_guests.html', guests=Guest.query.all(), groups=GuestGroup.query.all())

@app.route('/admin/add_guest', methods=['POST'])
def add_guest():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    new_guest = Guest(
        name=request.form.get('name'),
        phone=request.form.get('phone'),
        group_id=request.form.get('group_id') or None
    )
    db.session.add(new_guest)
    db.session.commit()
    flash("Convidado adicionado!", "success")
    return redirect(url_for('admin_guests'))

# ... (mantive todas as outras rotas de admin groups, gifts, whatsapp, venue iguais às do seu arquivo anterior)

# =========================
# 🔧 Middleware e Erros
# =========================
@app.before_request
def create_admin():
    if not Admin.query.first():
        admin = Admin(username='admin', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/healthz')
def healthz():
    try:
        db.session.execute(text("SELECT 1")).scalar()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/agradecimento')
def agradecimento():
    """Página de agradecimento pelo presente"""
    return render_template('agradecimento.html')

@app.route('/agradecimento/<int:guest_id>')
def agradecimento_personalizado(guest_id):
    """Página de agradecimento personalizada (opcional)"""
    # Se quiser personalizar com nome do convidado
    guest = Guest.query.get_or_404(guest_id)
    return render_template('agradecimento.html', guest_name=guest.name)

