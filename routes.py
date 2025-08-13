from flask import render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from app import app
# Correção: A classe 'hospede' deve ser importada como 'Hospede' (com H maiúsculo),
# de acordo com as convenções de nomenclatura de classes em Python.
from models import db, AdminUser, Admin, Hospede, GuestGroup, GiftRegistry, VenueInfo
from send_whatsapp import send_bulk_whatsapp_messages, get_wedding_message

import logging
from sqlalchemy import text
from datetime import datetime, date, time
import os
from flask import current_app
import uuid
from werkzeug.utils import secure_filename

import locale
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')
except locale.Error:
    # Este aviso aparece em ambientes como o Render, onde o pacote de localidade não está instalado.
    # O código continua a funcionar, mas a formatação de datas com nomes de meses pode não funcionar
    # para todos os formatos se o locale for necessário.
    logging.warning("Locale 'pt_BR.utf8' not available in routes.py, date parsing for month names might fail.")


@app.template_filter('format_date_br')
def format_date_br(value):
    meses_map = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
        7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    if not value:
        return ""
    
    dia = value.day
    mes = meses_map.get(value.month)
    ano = value.year
    
    if mes:
        return f"{dia} de {mes} de {ano}"
    else:
        return value.strftime('%Y-%m-%d') if isinstance(value, date) else ""


@app.route('/')
def index():
    try:
        venue = VenueInfo.query.first()
        
        gifts = GiftRegistry.query.filter_by(is_active=True).order_by(GiftRegistry.id.desc()).limit(3).all()
        
        return render_template('index.html', venue=venue, gifts=gifts)
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao acessar dados na rota principal: {e}")
        return render_template('index.html', venue=None, gifts=[])
    finally:
        db.session.close()


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login do administrador"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"🔍 Tentativa de login: {username}")
        
        try:
            admin = Admin.query.filter_by(username=username).first()
            print(f"🔍 Admin encontrado: {admin}")
            
            if admin and check_password_hash(admin.password_hash, password):
                session['admin_id'] = admin.id
                session['admin_username'] = admin.username
                print(f"✅ Login bem-sucedido para: {username}")
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                print(f"❌ Credenciais inválidas para: {username}")
                flash('Usuário ou senha inválidos!', 'danger')
                
        except Exception as e:
            print(f"❌ Erro no login: {e}")
            flash(f'Erro interno: {str(e)}', 'danger')
            
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Logout do administrador"""
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    """Dashboard do administrador"""
    if 'admin_id' not in session:
        flash('Acesso negado! Faça login primeiro.', 'danger')
        return redirect(url_for('admin_login'))
    
    # Usando o nome de classe correto, 'Hospede'
    total_hospedes = Hospede.query.count()
    confirmed_hospedes = Hospede.query.filter_by(rsvp_status='confirmado').count()
    pending_hospedes = Hospede.query.filter_by(rsvp_status='pendente').count()
    declined_hospedes = Hospede.query.filter_by(rsvp_status='nao_confirmado').count()
    
    total_groups = GuestGroup.query.count()
    total_gifts = GiftRegistry.query.count()
    
    return render_template('admin_dashboard.html', 
                           total_hospedes=total_hospedes,
                           confirmed_hospedes=confirmed_hospedes,
                           pending_hospedes=pending_hospedes,
                           declined_hospedes=declined_hospedes,
                           total_groups=total_groups,
                           total_gifts=total_gifts)

@app.route('/admin/hospedes')
def admin_hospedes():
    """Gerenciar lista de convidados"""
    if 'admin_id' not in session:
        flash('Acesso negado! Faça login primeiro.', 'danger')
        return redirect(url_for('admin_login'))
    
    # Usando o nome de classe correto, 'Hospede'
    hospedes = Hospede.query.all()
    groups = GuestGroup.query.all()
    
    total_hospedes = len(hospedes)
    confirmed_hospedes = len([g for g in hospedes if g.rsvp_status == 'confirmado'])
    declined_hospedes = len([g for g in hospedes if g.rsvp_status == 'nao_confirmado'])
    pending_hospedes = len([g for g in hospedes if g.rsvp_status == 'pendente'])
    
    return render_template('admin_hospedes.html', 
                           hospedes=hospedes, 
                           groups=groups,
                           total_hospedes=total_hospedes,
                           confirmed_hospedes=confirmed_hospedes,
                           declined_hospedes=declined_hospedes,
                           pending_hospedes=pending_hospedes)

@app.route('/admin/add_hospede', methods=['POST'])
def add_hospede():
    """Adicionar novo convidado"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    name = request.form.get('name')
    phone = request.form.get('phone')
    group_id = request.form.get('group_id')
    
    if not name:
        flash('Nome é obrigatório!', 'danger')
        return redirect(url_for('admin_hospedes'))
    
    group_id = int(group_id) if group_id and group_id != '' else None
    
    # Usando o nome de classe correto, 'Hospede'
    novo_hospede = Hospede(
        name=name,
        phone=phone,
        group_id=group_id
    )
    
    db.session.add(novo_hospede)
    db.session.commit()
    
    flash(f'Convidado {name} adicionado com sucesso!', 'success')
    return redirect(url_for('admin_hospedes'))

@app.route('/admin/edit_hospede/<int:hospede_id>', methods=['POST'])
def edit_hospede(hospede_id):
    """Editar convidado"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    # Usando o nome de classe correto, 'Hospede'
    hospede_a_editar = Hospede.query.get_or_404(hospede_id)
    
    hospede_a_editar.name = request.form.get('name')
    hospede_a_editar.phone = request.form.get('phone')
    group_id = request.form.get('group_id')
    hospede_a_editar.group_id = int(group_id) if group_id and group_id != '' else None
    
    db.session.commit()
    
    flash(f'Convidado {hospede_a_editar.name} atualizado com sucesso!', 'success')
    return redirect(url_for('admin_hospedes'))

@app.route('/admin/delete_hospede/<int:hospede_id>', methods=['POST'])
def delete_hospede(hospede_id):
    """Deletar convidado"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    # Usando o nome de classe correto, 'Hospede'
    hospede_a_deletar = Hospede.query.get_or_404(hospede_id)
    name = hospede_a_deletar.name
    
    db.session.delete(hospede_a_deletar)
    db.session.commit()
    
    flash(f'Convidado {name} removido com sucesso!', 'success')
    return redirect(url_for('admin_hospedes'))

@app.route('/rsvp')
def rsvp():
    """Página de confirmação de presença"""
    return render_template('rsvp.html')

@app.route('/search_hospede', methods=['POST'])
def search_hospede():
    """Busca convidado por nome e retorna o grupo ou os indivíduos."""
    name = request.form.get('name', '').strip()
    
    if not name:
        return jsonify({'error': 'Nome é obrigatório'}), 400
    
    # Usando o nome de classe correto, 'Hospede'
    hospedes_list = Hospede.query.filter(Hospede.name.ilike(f'%{name}%')).all()
    
    if not hospedes_list:
        return jsonify({'error': 'Convidado não encontrado'}), 404
    
    unique_group_ids = {h.group_id for h in hospedes_list}
    
    if len(unique_group_ids) == 1 and hospedes_list[0].group_id is not None:
        hospede_reference = hospedes_list[0]
        # Usando o nome de classe correto, 'Hospede'
        group_hospedes = Hospede.query.filter_by(group_id=hospede_reference.group_id).all()
        group_name = hospede_reference.group.name if hospede_reference.group else None
    else:
        group_hospedes = hospedes_list
        group_name = None
    
    hospedes_data = [{
        'id': h.id,
        'name': h.name,
        'phone': h.phone,
        'rsvp_status': h.rsvp_status
    } for h in group_hospedes]
    
    return jsonify({
        'hospedes': hospedes_data,
        'group_name': group_name
    })

@app.route('/confirm_rsvp', methods=['POST'])
def confirm_rsvp():
    """Confirmar presença dos convidados"""
    hospede_ids = request.form.getlist('hospede_ids')
    
    if not hospede_ids:
        flash('Nenhum convidado selecionado!', 'danger')
        return redirect(url_for('rsvp'))
    
    confirmed_hospedes = []
    declined_hospedes = []
    
    for hospede_id in hospede_ids:
        # Usando o nome de classe correto, 'Hospede'
        hospede_obj = Hospede.query.get(hospede_id)
        if hospede_obj:
            rsvp_choice = request.form.get(f'rsvp_{hospede_id}')
            
            if rsvp_choice in ['confirmado', 'nao_confirmado']:
                hospede_obj.rsvp_status = rsvp_choice
                if rsvp_choice == 'confirmado':
                    confirmed_hospedes.append(hospede_obj)
                else:
                    declined_hospedes.append(hospede_obj)
    
    db.session.commit()
    
    return render_template('rsvp_success.html', 
                           confirmed_hospedes=confirmed_hospedes,
                           declined_hospedes=declined_hospedes)

@app.route('/admin/groups')
def admin_groups():
    """Gerenciar grupos de convidados"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    groups = GuestGroup.query.all()
    return render_template('admin_groups.html', groups=groups)

@app.route('/admin/add_group', methods=['POST'])
def add_group():
    """Adicionar novo grupo"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    name = request.form.get('name')
    description = request.form.get('description')
    
    if not name:
        flash('Nome do grupo é obrigatório!', 'danger')
        return redirect(url_for('admin_groups'))
    
    group = GuestGroup(
        name=name,
        description=description
    )
    
    db.session.add(group)
    db.session.commit()
    
    flash(f'Grupo {name} criado com sucesso!', 'success')
    return redirect(url_for('admin_groups'))

@app.route('/admin/edit_group/<int:group_id>', methods=['POST'])
def edit_group(group_id):
    """Editar grupo"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    group = GuestGroup.query.get_or_404(group_id)
    
    group.name = request.form.get('name')
    group.description = request.form.get('description')
    
    db.session.commit()
    
    flash(f'Grupo {group.name} atualizado com sucesso!', 'success')
    return redirect(url_for('admin_groups'))

@app.route('/admin/delete_group/<int:group_id>', methods=['POST'])
def delete_group(group_id):
    """Deletar grupo"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    group = GuestGroup.query.get_or_404(group_id)
    name = group.name
    
    # Usando o relacionamento 'hospedes' que já está definido no modelo
    for hospede_obj in group.hospedes:
        hospede_obj.group_id = None
    
    db.session.delete(group)
    db.session.commit()
    
    flash(f'Grupo {name} removido com sucesso!', 'success')
    return redirect(url_for('admin_groups'))

@app.route('/admin/venue')
def admin_venue():
    """Gerenciar informações do local"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    venue = VenueInfo.query.first()
    return render_template('admin_venue.html', venue=venue)

@app.route('/admin/update_venue', methods=['POST'])
def update_venue():
    """Gerenciar informações do local (POST)"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))

    venue = VenueInfo.query.first()
    if venue is None:
        venue = VenueInfo()
        db.session.add(venue)

    meses_map = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,
        'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }

    try:
        venue.name = request.form.get('name')
        venue.address = request.form.get('address')
        venue.map_link = request.form.get('map_link')
        venue.description = request.form.get('description')
        
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        event_datetime_str = request.form.get('event_datetime')
        
        if date_str:
            partes = date_str.lower().replace(' de ', ' ').split()
            if len(partes) == 3:
                dia = int(partes[0])
                mes_nome = partes[1]
                ano = int(partes[2])
                mes = meses_map.get(mes_nome)
                if mes:
                    venue.date = date(ano, mes, dia)
                else:
                    raise ValueError("Nome do mês inválido.")
            else:
                raise ValueError("Formato de data inválido.")
        else:
            venue.date = None
        
        if time_str:
            time_str_clean = time_str.replace(" da manhã", "").replace(" da noite", "").strip()
            venue.time = datetime.strptime(time_str_clean, "%H:%M").time()
        else:
            venue.time = None
        
        if event_datetime_str:
            venue.event_datetime = datetime.fromisoformat(event_datetime_str)
        else:
            venue.event_datetime = None
            
        db.session.commit()
        flash("Local do evento atualizado com sucesso!", "success")
    
    except ValueError as e:
        db.session.rollback()
        logging.error(f"Erro de formato de data/hora: {e}")
        flash("Erro: verifique os formatos de Data (Ex: 19 de Outubro de 2025) e Hora (Ex: 18:30).", "danger")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao salvar informações do local: {e}")
        flash(f"Erro ao salvar as informações. Tente novamente. Detalhes: {str(e)}", "danger")

    return redirect(url_for('admin_venue'))
    
@app.route('/admin/gifts')
def admin_gifts():
    """Gerenciar lista de presentes"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    gifts = GiftRegistry.query.all()
    return render_template('admin_gifts.html', gifts=gifts)

@app.route('/admin/add_gift', methods=['POST'])
def add_gift():
    """Adicionar presente"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    item_name = request.form.get('item_name')
    description = request.form.get('description')
    price = request.form.get('price')
    image_url = request.form.get('image_url')
    pix_key = request.form.get('pix_key')
    pix_link = request.form.get('pix_link')
    credit_card_link = request.form.get('credit_card_link')
    
    if not item_name:
        flash('Nome do presente é obrigatório!', 'danger')
        return redirect(url_for('admin_gifts'))
    
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            file_ext = os.path.splitext(secure_filename(file.filename))[1].lower()
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                image_filename = f"{uuid.uuid4().hex}{file_ext}"
                file_path = os.path.join('static/uploads/gifts', image_filename)
                
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
    
    gift = GiftRegistry(
        item_name=item_name,
        description=description,
        price=price,
        image_url=image_url,
        pix_key=pix_key,
        pix_link=pix_link,
        credit_card_link=credit_card_link,
        image_filename=image_filename
    )
    
    db.session.add(gift)
    db.session.commit()
    
    flash(f'Presente {item_name} adicionado com sucesso!', 'success')
    return redirect(url_for('admin_gifts'))

@app.route('/admin/edit_gift/<int:gift_id>', methods=['POST'])
def edit_gift(gift_id):
    """Editar presente"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    gift = GiftRegistry.query.get_or_404(gift_id)
    
    gift.item_name = request.form.get('item_name')
    gift.description = request.form.get('description')
    gift.price = request.form.get('price')
    gift.image_url = request.form.get('image_url')
    gift.pix_key = request.form.get('pix_key')
    gift.pix_link = request.form.get('pix_link')
    gift.credit_card_link = request.form.get('credit_card_link')
    gift.is_active = bool(request.form.get('is_active'))
    
    db.session.commit()
    
    flash(f'Presente {gift.item_name} atualizado com sucesso!', 'success')
    return redirect(url_for('admin_gifts'))

@app.route('/admin/delete_gift/<int:gift_id>', methods=['POST'])
def delete_gift(gift_id):
    """Deletar presente"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    gift = GiftRegistry.query.get_or_404(gift_id)
    name = gift.item_name
    
    db.session.delete(gift)
    db.session.commit()
    
    flash(f'Presente {name} removido com sucesso!', 'success')
    return redirect(url_for('admin_gifts'))

@app.route('/gifts')
def gifts():
    """Página pública da lista de presentes"""
    gifts = GiftRegistry.query.filter_by(is_active=True).all()
    return render_template('gifts.html', gifts=gifts)

@app.route('/api/event-datetime')
def api_event_datetime():
    """API para obter a data do evento para contagem regressiva"""
    venue = VenueInfo.query.first()
    if venue and venue.event_datetime:
        return jsonify({
            'datetime': venue.event_datetime.isoformat(),
            'success': True
        })
    else:
        return jsonify({
            'datetime': '2025-10-19T08:30:00',
            'success': True
        })

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    """Página de configurações do administrador"""
    if 'admin_id' not in session:
        flash('Acesso negado! Faça login primeiro.', 'danger')
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            flash('Todos os campos são obrigatórios!', 'danger')
            return render_template('admin_settings.html')
        
        admin = Admin.query.get(session['admin_id'])
        if not check_password_hash(admin.password_hash, current_password):
            flash('Senha atual incorreta!', 'danger')
            return render_template('admin_settings.html')
        
        if new_password != confirm_password:
            flash('As novas senhas não coincidem!', 'danger')
            return render_template('admin_settings.html')
        
        if len(new_password) < 6:
            flash('A nova senha deve ter pelo menos 6 caracteres!', 'danger')
            return render_template('admin_settings.html')
        
        admin.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin_settings.html')

@app.route('/admin/whatsapp')
def admin_whatsapp():
    """Página para envio de mensagens WhatsApp"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    # Usando o nome de classe correto, 'Hospede'
    hospedes = Hospede.query.filter(Hospede.phone.isnot(None)).all()
    groups = GuestGroup.query.all()
    venue = VenueInfo.query.first()
    
    return render_template('admin_whatsapp.html', hospedes=hospedes, groups=groups, venue=venue)

@app.route('/admin/send_whatsapp', methods=['POST'])
def send_whatsapp():
    """Enviar mensagem WhatsApp"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    data = request.get_json()
    
    recipient_type = data.get('recipient_type')
    message = data.get('message')
    message_type = data.get('message_type', 'custom')
    
    if not message:
        return jsonify({'error': 'Mensagem é obrigatória'}), 400
    
    phone_numbers = []
    
    if recipient_type == 'individual':
        hospede_id = data.get('hospede_id')
        # Usando o nome de classe correto, 'Hospede'
        hospede_obj = Hospede.query.get(hospede_id)
        if hospede_obj and hospede_obj.phone:
            phone_numbers.append(hospede_obj.phone)
    
    elif recipient_type == 'group':
        group_id = data.get('group_id')
        group = GuestGroup.query.get(group_id)
        if group:
            phone_numbers = [h.phone for h in group.hospedes if h.phone]
    
    elif recipient_type == 'all':
        # Usando o nome de classe correto, 'Hospede'
        hospedes_with_phone = Hospede.query.filter(Hospede.phone.isnot(None)).all()
        phone_numbers = [h.phone for h in hospedes_with_phone]
    
    elif recipient_type == 'status':
        status = data.get('status')
        # Usando o nome de classe correto, 'Hospede'
        hospedes_with_status = Hospede.query.filter(Hospede.rsvp_status == status, Hospede.phone.isnot(None)).all()
        phone_numbers = [h.phone for h in hospedes_with_status]
    
    if not phone_numbers:
        return jsonify({'error': 'Nenhum número de telefone encontrado'}), 400
    
    if message_type != 'custom':
        venue = VenueInfo.query.first()
        if venue:
            message = get_wedding_message(message_type,
                                         date=venue.date,
                                         time=venue.time,
                                         venue=venue.name,
                                         address=venue.address,
                                         rsvp_link=request.url_root + 'rsvp',
                                         gift_link=request.url_root + 'gifts')
    
    results = send_bulk_whatsapp_messages(phone_numbers, message)
    
    return jsonify({
        'success': True,
        'results': results
    })

@app.route('/admin/group_hospedes/<int:group_id>')
def get_group_hospedes(group_id):
    """API para obter os convidados de um grupo específico."""
    if 'admin_id' not in session:
        return jsonify({'error': 'Acesso negado'}), 403
    
    group = GuestGroup.query.get_or_404(group_id)
    hospedes_data = [{
        'id': hospede_obj.id,
        'name': hospede_obj.name,
        'phone': hospede_obj.phone,
        'rsvp_status': hospede_obj.rsvp_status,
        'group_name': group.name
    } for hospede_obj in group.hospedes]
    
    return jsonify({'hospedes': hospedes_data})

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.before_request
def create_admin():
    """Criar admin se não existir"""
    try:
        if not Admin.query.first():
            admin = Admin(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin criado automaticamente")
    except Exception as e:
        print(f"Erro ao criar admin: {e}")

@app.route('/healthz')
def healthz():
    """
    Verifica a saúde básica do aplicativo e a conexão com o banco de dados (Supabase).
    O objetivo principal é responder 200 OK para manter o serviço ativo e
    verificar a conectividade crítica.
    """
    try:
        db.session.execute(text("SELECT 1")).scalar()
        
        if not os.environ.get("DATABASE_URL"):
            raise ValueError("DATABASE_URL environment variable is missing.")

        return jsonify({
            "status": "ok",
            "message": "Application is healthy and database is connected."
        }), 200

    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "error",
            "message": f"Application unhealthy or critical component failed: {str(e)}"
        }), 500
