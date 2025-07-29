from flask import render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, db
from models import Admin, Guest, GuestGroup, VenueInfo, GiftRegistry
from send_whatsapp import send_whatsapp_message, send_bulk_whatsapp_messages, get_wedding_message
import json

@app.route('/')
def index():
    """Página inicial com informações do casamento"""
    venue = VenueInfo.query.first()
    gifts = GiftRegistry.query.filter_by(is_active=True).limit(3).all()
    return render_template('index.html', venue=venue, gifts=gifts)

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
    
    # Estatísticas
    total_guests = Guest.query.count()
    confirmed_guests = Guest.query.filter_by(rsvp_status='confirmado').count()
    pending_guests = Guest.query.filter_by(rsvp_status='pendente').count()
    declined_guests = Guest.query.filter_by(rsvp_status='nao_confirmado').count()
    
    total_groups = GuestGroup.query.count()
    total_gifts = GiftRegistry.query.count()
    
    return render_template('admin_dashboard.html', 
                         total_guests=total_guests,
                         confirmed_guests=confirmed_guests,
                         pending_guests=pending_guests,
                         declined_guests=declined_guests,
                         total_groups=total_groups,
                         total_gifts=total_gifts)

@app.route('/admin/guests')
def admin_guests():
    """Gerenciar lista de convidados"""
    if 'admin_id' not in session:
        flash('Acesso negado! Faça login primeiro.', 'danger')
        return redirect(url_for('admin_login'))
    
    guests = Guest.query.all()
    groups = GuestGroup.query.all()
    
    # Estatísticas
    total_guests = len(guests)
    confirmed_guests = len([g for g in guests if g.rsvp_status == 'confirmado'])
    declined_guests = len([g for g in guests if g.rsvp_status == 'nao_confirmado'])
    pending_guests = len([g for g in guests if g.rsvp_status == 'pendente'])
    
    return render_template('admin_guests.html', 
                         guests=guests, 
                         groups=groups,
                         total_guests=total_guests,
                         confirmed_guests=confirmed_guests,
                         declined_guests=declined_guests,
                         pending_guests=pending_guests)

@app.route('/admin/add_guest', methods=['POST'])
def add_guest():
    """Adicionar novo convidado"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    name = request.form.get('name')
    phone = request.form.get('phone')
    group_id = request.form.get('group_id')
    
    if not name:
        flash('Nome é obrigatório!', 'danger')
        return redirect(url_for('admin_guests'))
    
    # Converte group_id para int ou None
    group_id = int(group_id) if group_id and group_id != '' else None
    
    guest = Guest(
        name=name,
        phone=phone,
        group_id=group_id
    )
    
    db.session.add(guest)
    db.session.commit()
    
    flash(f'Convidado {name} adicionado com sucesso!', 'success')
    return redirect(url_for('admin_guests'))

@app.route('/admin/edit_guest/<int:guest_id>', methods=['POST'])
def edit_guest(guest_id):
    """Editar convidado"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    guest = Guest.query.get_or_404(guest_id)
    
    guest.name = request.form.get('name')
    guest.phone = request.form.get('phone')
    group_id = request.form.get('group_id')
    guest.group_id = int(group_id) if group_id and group_id != '' else None
    
    db.session.commit()
    
    flash(f'Convidado {guest.name} atualizado com sucesso!', 'success')
    return redirect(url_for('admin_guests'))

@app.route('/admin/delete_guest/<int:guest_id>', methods=['POST'])
def delete_guest(guest_id):
    """Deletar convidado"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    guest = Guest.query.get_or_404(guest_id)
    name = guest.name
    
    db.session.delete(guest)
    db.session.commit()
    
    flash(f'Convidado {name} removido com sucesso!', 'success')
    return redirect(url_for('admin_guests'))

@app.route('/rsvp')
def rsvp():
    """Página de confirmação de presença"""
    return render_template('rsvp.html')

@app.route('/search_guest', methods=['POST'])
def search_guest():
    """Buscar convidado por nome (API)"""
    name = request.form.get('name', '').strip()
    
    if not name:
        return jsonify({'error': 'Nome é obrigatório'}), 400
    
    # Busca por nome (case-insensitive)
    guest = Guest.query.filter(Guest.name.ilike(f'%{name}%')).first()
    
    if not guest:
        return jsonify({'error': 'Convidado não encontrado'}), 404
    
    # Se o convidado pertence a um grupo, busca todos os membros do grupo
    if guest.group_id:
        group_guests = Guest.query.filter_by(group_id=guest.group_id).all()
        group_name = guest.group.name if guest.group else None
    else:
        group_guests = [guest]
        group_name = None
    
    guests_data = [{
        'id': g.id,
        'name': g.name,
        'phone': g.phone,
        'rsvp_status': g.rsvp_status
    } for g in group_guests]
    
    return jsonify({
        'guests': guests_data,
        'group_name': group_name
    })

@app.route('/confirm_rsvp', methods=['POST'])
def confirm_rsvp():
    """Confirmar presença dos convidados"""
    # Obter IDs dos convidados
    guest_ids = request.form.getlist('guest_ids')
    
    if not guest_ids:
        flash('Nenhum convidado selecionado!', 'danger')
        return redirect(url_for('rsvp'))
    
    confirmed_guests = []
    declined_guests = []
    
    # Processar cada convidado
    for guest_id in guest_ids:
        guest = Guest.query.get(guest_id)
        if guest:
            # Verificar o status escolhido
            rsvp_choice = request.form.get(f'rsvp_{guest_id}')
            
            if rsvp_choice in ['confirmado', 'nao_confirmado']:
                guest.rsvp_status = rsvp_choice
                if rsvp_choice == 'confirmado':
                    confirmed_guests.append(guest)
                else:
                    declined_guests.append(guest)
    
    db.session.commit()
    
    return render_template('rsvp_success.html', 
                         confirmed_guests=confirmed_guests,
                         declined_guests=declined_guests)

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
    
    # Remove a associação dos convidados com o grupo
    for guest in group.guests:
        guest.group_id = None
    
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
    """Atualizar informações do local"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    venue = VenueInfo.query.first()
    
    if not venue:
        venue = VenueInfo()
        db.session.add(venue)
    
    venue.name = request.form.get('name')
    venue.address = request.form.get('address')
    venue.map_link = request.form.get('map_link')
    venue.description = request.form.get('description')
    venue.date = request.form.get('date')
    venue.time = request.form.get('time')
    
    # Lidar com event_datetime
    event_datetime_str = request.form.get('event_datetime')
    if event_datetime_str:
        from datetime import datetime
        venue.event_datetime = datetime.fromisoformat(event_datetime_str)
    
    db.session.commit()
    
    flash('Informações do local atualizadas com sucesso!', 'success')
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
    
    # Lidar com upload de imagem
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            import os
            import uuid
            from werkzeug.utils import secure_filename
            
            # Gerar nome único para o arquivo
            file_ext = os.path.splitext(secure_filename(file.filename))[1].lower()
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                image_filename = f"{uuid.uuid4().hex}{file_ext}"
                file_path = os.path.join('static/uploads/gifts', image_filename)
                
                # Criar diretório se não existir
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
        # Data padrão caso não esteja configurada
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
        
        # Verificar senha atual
        admin = Admin.query.get(session['admin_id'])
        if not check_password_hash(admin.password_hash, current_password):
            flash('Senha atual incorreta!', 'danger')
            return render_template('admin_settings.html')
        
        # Verificar se as novas senhas coincidem
        if new_password != confirm_password:
            flash('As novas senhas não coincidem!', 'danger')
            return render_template('admin_settings.html')
        
        # Verificar se a nova senha tem pelo menos 6 caracteres
        if len(new_password) < 6:
            flash('A nova senha deve ter pelo menos 6 caracteres!', 'danger')
            return render_template('admin_settings.html')
        
        # Atualizar senha
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
    
    guests = Guest.query.filter(Guest.phone.isnot(None)).all()
    groups = GuestGroup.query.all()
    venue = VenueInfo.query.first()
    
    return render_template('admin_whatsapp.html', guests=guests, groups=groups, venue=venue)

@app.route('/admin/send_whatsapp', methods=['POST'])
def send_whatsapp():
    """Enviar mensagem WhatsApp"""
    if 'admin_id' not in session:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('admin_login'))
    
    data = request.get_json()
    
    recipient_type = data.get('recipient_type')  # 'individual', 'group', 'all'
    message = data.get('message')
    message_type = data.get('message_type', 'custom')
    
    if not message:
        return jsonify({'error': 'Mensagem é obrigatória'}), 400
    
    phone_numbers = []
    
    if recipient_type == 'individual':
        guest_id = data.get('guest_id')
        guest = Guest.query.get(guest_id)
        if guest and guest.phone:
            phone_numbers.append(guest.phone)
    
    elif recipient_type == 'group':
        group_id = data.get('group_id')
        group = GuestGroup.query.get(group_id)
        if group:
            phone_numbers = [g.phone for g in group.guests if g.phone]
    
    elif recipient_type == 'all':
        guests = Guest.query.filter(Guest.phone.isnot(None)).all()
        phone_numbers = [g.phone for g in guests]
    
    elif recipient_type == 'status':
        status = data.get('status')
        guests = Guest.query.filter(Guest.rsvp_status == status, Guest.phone.isnot(None)).all()
        phone_numbers = [g.phone for g in guests]
    
    if not phone_numbers:
        return jsonify({'error': 'Nenhum número de telefone encontrado'}), 400
    
    # Formatar mensagem se for pré-definida
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
    
    # Enviar mensagens
    results = send_bulk_whatsapp_messages(phone_numbers, message)
    
    return jsonify({
        'success': True,
        'results': results
    })

@app.route('/admin/group_guests/<int:group_id>')
def get_group_guests(group_id):
    """API para obter convidados do grupo e disponíveis"""
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    group = GuestGroup.query.get_or_404(group_id)
    
    # Convidados do grupo
    group_guests = [{
        'id': guest.id,
        'name': guest.name,
        'rsvp_status': guest.rsvp_status
    } for guest in group.guests]
    
    # Convidados disponíveis (sem grupo)
    available_guests = [{
        'id': guest.id,
        'name': guest.name,
        'rsvp_status': guest.rsvp_status
    } for guest in Guest.query.filter_by(group_id=None).all()]
    
    return jsonify({
        'group_guests': group_guests,
        'available_guests': available_guests
    })

@app.route('/admin/add_guest_to_group', methods=['POST'])
def add_guest_to_group():
    """Adicionar convidado ao grupo"""
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    guest_id = data.get('guest_id')
    group_id = data.get('group_id')
    
    if not guest_id or not group_id:
        return jsonify({'error': 'Missing data'}), 400
    
    guest = Guest.query.get_or_404(guest_id)
    group = GuestGroup.query.get_or_404(group_id)
    
    # Adicionar convidado ao grupo
    guest.group_id = group_id
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/admin/remove_guest_from_group', methods=['POST'])
def remove_guest_from_group():
    """Remover convidado do grupo"""
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    guest_id = data.get('guest_id')
    
    if not guest_id:
        return jsonify({'error': 'Missing data'}), 400
    
    guest = Guest.query.get_or_404(guest_id)
    
    # Remover convidado do grupo
    guest.group_id = None
    db.session.commit()
    
    return jsonify({'success': True})

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.before_first_request
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
