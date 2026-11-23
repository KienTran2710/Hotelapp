from datetime import datetime, date, timedelta
from flask import render_template, request, redirect, session
from hotelapp import app, dao


@app.context_processor
def common_context():
    return {
        'room_types': dao.load_room_types(),
        'customer_types': dao.load_customer_types(),
        'regulation': dao.get_regulation()
    }


@app.route('/')
def index():
    rooms = dao.load_rooms(
        kw=request.args.get('kw'),
        room_type_id=request.args.get('room_type_id'),
        min_price=request.args.get('min_price'),
        max_price=request.args.get('max_price'),
        status=request.args.get('status')
    )
    return render_template('index.html', rooms=rooms)


@app.route('/booking', methods=['GET', 'POST'])
def booking_view():
    err_msg = None
    success_msg = None

    if request.method == 'POST':
        try:
            booker_name = request.form.get('booker_name', '')
            checkin_str = request.form.get('checkin_date')
            checkout_str = request.form.get('checkout_date')
            selected_rooms = request.form.getlist('room_ids')

            checkin_date = datetime.strptime(checkin_str, '%Y-%m-%d').date()
            checkout_date = datetime.strptime(checkout_str, '%Y-%m-%d').date()

            reg = dao.get_regulation()
            room_guests_map = {}

            for rid in selected_rooms:
                guests = []
                for idx in range(1, reg.max_guests_per_room + 1):
                    g_name = request.form.get(f'guest_name_{rid}_{idx}', '').strip()
                    g_type = request.form.get(f'guest_type_{rid}_{idx}')
                    g_cmnd = request.form.get(f'guest_cmnd_{rid}_{idx}', '').strip()
                    g_addr = request.form.get(f'guest_addr_{rid}_{idx}', '').strip()
                    if g_name:
                        guests.append({
                            'guest_name': g_name,
                            'customer_type_id': g_type,
                            'identity_card': g_cmnd,
                            'address': g_addr
                        })
                if not guests:
                    guests.append({
                        'guest_name': booker_name.strip(),
                        'customer_type_id': dao.load_customer_types()[0].id,
                        'identity_card': '',
                        'address': ''
                    })
                room_guests_map[int(rid)] = guests

            bk = dao.create_booking(
                booker_name=booker_name,
                checkin_date=checkin_date,
                checkout_date=checkout_date,
                room_guests_map=room_guests_map,
                user_id=session.get('user_id')
            )
            success_msg = f"Lap phieu dat phong #{bk.id} thanh cong!"
        except Exception as ex:
            err_msg = str(ex)

    available_rooms = dao.load_rooms(status='TRONG')
    bookings = dao.load_bookings()
    preselect_room_id = request.args.get('room_id', type=int)

    return render_template(
        'booking.html',
        available_rooms=available_rooms,
        bookings=bookings,
        preselect_room_id=preselect_room_id,
        today=date.today().isoformat(),
        tomorrow=(date.today() + timedelta(days=1)).isoformat(),
        err_msg=err_msg,
        success_msg=success_msg
    )


@app.route('/rental', methods=['GET', 'POST'])
def rental_view():
    err_msg = None
    success_msg = None

    if request.method == 'POST':
        try:
            booking_id = request.form.get('booking_id') or None
            checkin_str = request.form.get('checkin_date')
            checkout_str = request.form.get('checkout_date')
            selected_rooms = request.form.getlist('room_ids')

            checkin_date = datetime.strptime(checkin_str, '%Y-%m-%d').date()
            checkout_date = datetime.strptime(checkout_str, '%Y-%m-%d').date()

            reg = dao.get_regulation()
            room_guests_map = {}

            for rid in selected_rooms:
                guests = []
                for idx in range(1, reg.max_guests_per_room + 1):
                    g_name = request.form.get(f'guest_name_{rid}_{idx}', '').strip()
                    g_type = request.form.get(f'guest_type_{rid}_{idx}')
                    g_cmnd = request.form.get(f'guest_cmnd_{rid}_{idx}', '').strip()
                    g_addr = request.form.get(f'guest_addr_{rid}_{idx}', '').strip()
                    if g_name:
                        guests.append({
                            'guest_name': g_name,
                            'customer_type_id': g_type,
                            'identity_card': g_cmnd,
                            'address': g_addr
                        })
                room_guests_map[int(rid)] = guests

            rt = dao.create_rental(
                checkin_date=checkin_date,
                checkout_date=checkout_date,
                room_guests_map=room_guests_map,
                booking_id=booking_id,
                staff_id=session.get('user_id')
            )
            success_msg = f"Lap phieu thue phong #{rt.id} thanh cong!"
        except Exception as ex:
            err_msg = str(ex)

    kw_booking = request.args.get('kw_booking')
    pending_bookings = dao.load_bookings(kw=kw_booking, status='CHO_NHAN')

    selected_booking = None
    booking_id_param = request.args.get('booking_id')
    if booking_id_param:
        selected_booking = dao.get_booking_by_id(booking_id_param)

    available_rooms = dao.load_rooms(status='TRONG')
    active_rentals = dao.load_active_rentals()

    return render_template(
        'rental.html',
        pending_bookings=pending_bookings,
        selected_booking=selected_booking,
        available_rooms=available_rooms,
        active_rentals=active_rentals,
        kw_booking=kw_booking or '',
        today=date.today().isoformat(),
        tomorrow=(date.today() + timedelta(days=1)).isoformat(),
        err_msg=err_msg,
        success_msg=success_msg
    )


@app.route('/payment', methods=['GET', 'POST'])
def payment_view():
    err_msg = None
    success_msg = None

    if request.method == 'POST':
        try:
            rental_id = request.form.get('rental_id')
            checkout_str = request.form.get('actual_checkout')
            actual_checkout = datetime.strptime(checkout_str, '%Y-%m-%d').date() if checkout_str else None
            inv = dao.pay_rental(rental_id, actual_checkout=actual_checkout, staff_id=session.get('user_id'))
            success_msg = f"Thanh toan thanh cong! Ma hoa don: #{inv.id}"
        except Exception as ex:
            err_msg = str(ex)

    active_rentals = dao.load_active_rentals()
    rental_id_param = request.args.get('rental_id')
    checkout_param = request.args.get('actual_checkout')

    if not rental_id_param and active_rentals:
        rental_id_param = active_rentals[0].id

    bill = None
    if rental_id_param:
        actual_dt = datetime.strptime(checkout_param, '%Y-%m-%d').date() if checkout_param else None
        bill = dao.calculate_rental_bill(rental_id_param, actual_checkout=actual_dt)

    invoices = dao.load_invoices()

    return render_template(
        'payment.html',
        active_rentals=active_rentals,
        bill=bill,
        invoices=invoices,
        err_msg=err_msg,
        success_msg=success_msg
    )


@app.route('/stats')
def stats_view():
    today = date.today()
    month = request.args.get('month', default=today.month, type=int)
    year = request.args.get('year', default=today.year, type=int)

    revenue_rows, total_revenue = dao.stats_revenue_by_month(month, year)
    density_rows, days_in_month = dao.stats_room_density_by_month(month, year)

    return render_template(
        'stats.html',
        month=month,
        year=year,
        revenue_rows=revenue_rows,
        total_revenue=total_revenue,
        density_rows=density_rows,
        days_in_month=days_in_month
    )


@app.route('/login', methods=['GET', 'POST'])
def login_view():
    err_msg = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        user = dao.auth_user(username, password)
        if user:
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['role'] = user.role
            return redirect('/')
        err_msg = 'Ten dang nhap hoac mat khau khong dung!'
    return render_template('login.html', err_msg=err_msg)


@app.route('/register', methods=['GET', 'POST'])
def register_view():
    err_msg = None
    if request.method == 'POST':
        name = request.form.get('name', '')
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        if password != confirm:
            err_msg = 'Mat khau xac nhan khong khop!'
        else:
            user = dao.register_user(name, username, password)
            if user:
                return redirect('/login')
            err_msg = 'Ten dang nhap da ton tai!'
    return render_template('register.html', err_msg=err_msg)


@app.route('/logout')
def logout_view():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    with app.app_context():
        from hotelapp import admin
        app.run(debug=True)
