import calendar
from datetime import date
from sqlalchemy import extract
from werkzeug.security import generate_password_hash, check_password_hash
from hotelapp import db
from hotelapp.models import (
    User, Regulation, RoomType, CustomerType, Room,
    Booking, BookingDetail, BookingGuest,
    Rental, RentalDetail, RentalGuest, Invoice
)


def get_regulation():
    reg = Regulation.query.first()
    if not reg:
        reg = Regulation(max_guests_per_room=3, standard_guests=2, surcharge_rate=0.25, max_advance_days=28)
        db.session.add(reg)
        db.session.commit()
    return reg


def load_room_types():
    return RoomType.query.all()


def load_customer_types():
    return CustomerType.query.all()


def load_rooms(kw=None, room_type_id=None, min_price=None, max_price=None, status=None):
    query = Room.query.join(RoomType)

    if kw:
        query = query.filter(Room.name.contains(kw))

    if room_type_id:
        query = query.filter(Room.room_type_id == int(room_type_id))

    if min_price:
        query = query.filter(RoomType.price >= float(min_price))

    if max_price:
        query = query.filter(RoomType.price <= float(max_price))

    if status:
        query = query.filter(Room.status == status)

    return query.order_by(Room.name).all()


def auth_user(username, password):
    user = User.query.filter_by(username=username.strip(), active=True).first()
    if user and check_password_hash(user.password, password):
        return user
    return None


def register_user(name, username, password):
    if User.query.filter_by(username=username.strip()).first():
        return None
    user = User(
        name=name.strip(),
        username=username.strip(),
        password=generate_password_hash(password),
        role='CUSTOMER'
    )
    db.session.add(user)
    db.session.commit()
    return user


def create_booking(booker_name, checkin_date, checkout_date, room_guests_map, user_id=None):
    reg = get_regulation()
    today = date.today()

    if checkout_date <= checkin_date:
        raise ValueError("Ngay tra phong phai sau ngay nhan phong.")

    advance_days = (checkin_date - today).days
    if advance_days < 0:
        raise ValueError("Ngay nhan phong khong duoc o trong qua khu.")
    if advance_days > reg.max_advance_days:
        raise ValueError(f"Thoi diem nhan phong khong duoc qua {reg.max_advance_days} ngay ke tu ngay dat.")

    if not room_guests_map:
        raise ValueError("Vui long chon it nhat 1 phong trong.")

    booking = Booking(
        booker_name=booker_name.strip(),
        booking_date=today,
        checkin_date=checkin_date,
        checkout_date=checkout_date,
        status='CHO_NHAN',
        user_id=user_id
    )
    db.session.add(booking)
    db.session.flush()

    for room_id, guests in room_guests_map.items():
        room = Room.query.get(int(room_id))
        if not room or room.status != 'TRONG':
            raise ValueError(f"Phong {room.name if room else room_id} khong con trong.")

        if len(guests) > reg.max_guests_per_room:
            raise ValueError(f"Phong {room.name} vuot qua so khach toi da ({reg.max_guests_per_room} khach).")

        detail = BookingDetail(booking_id=booking.id, room_id=room.id)
        db.session.add(detail)
        db.session.flush()

        for g in guests:
            bg = BookingGuest(
                booking_detail_id=detail.id,
                guest_name=g['guest_name'].strip(),
                customer_type_id=int(g['customer_type_id']),
                identity_card=g.get('identity_card', '').strip(),
                address=g.get('address', '').strip()
            )
            db.session.add(bg)

        room.status = 'DA_DAT'

    db.session.commit()
    return booking


def load_bookings(kw=None, status=None):
    query = Booking.query
    if status:
        query = query.filter(Booking.status == status)
    if kw:
        query = query.filter(Booking.booker_name.contains(kw))
    return query.order_by(Booking.id.desc()).all()


def get_booking_by_id(booking_id):
    return Booking.query.get(int(booking_id))


def create_rental(checkin_date, checkout_date, room_guests_map, booking_id=None, staff_id=None):
    reg = get_regulation()

    if checkout_date <= checkin_date:
        raise ValueError("Ngay tra phong phai sau ngay nhan phong.")
    if not room_guests_map:
        raise ValueError("Vui long chon it nhat 1 phong thue.")

    booking = None
    if booking_id:
        booking = Booking.query.get(int(booking_id))

    rental = Rental(
        booking_id=booking.id if booking else None,
        staff_id=staff_id,
        checkin_date=checkin_date,
        checkout_date=checkout_date,
        status='DANG_THUE'
    )
    db.session.add(rental)
    db.session.flush()

    for room_id, guests in room_guests_map.items():
        room = Room.query.get(int(room_id))
        if not room:
            raise ValueError("Phong khong ton tai.")
        if not booking and room.status != 'TRONG':
            raise ValueError(f"Phong {room.name} hien khong trong.")
        if not guests:
            raise ValueError(f"Phong {room.name} phai co it nhat 1 khach.")
        if len(guests) > reg.max_guests_per_room:
            raise ValueError(f"Phong {room.name} vuot qua {reg.max_guests_per_room} khach.")

        max_coeff = 1.0
        for g in guests:
            ct = CustomerType.query.get(int(g['customer_type_id']))
            if ct and ct.coefficient > max_coeff:
                max_coeff = ct.coefficient

        surcharge = reg.surcharge_rate if len(guests) > reg.standard_guests else 0.0

        detail = RentalDetail(
            rental_id=rental.id,
            room_id=room.id,
            unit_price=room.price,
            surcharge_rate=surcharge,
            customer_coefficient=max_coeff
        )
        db.session.add(detail)
        db.session.flush()

        for g in guests:
            rg = RentalGuest(
                rental_detail_id=detail.id,
                guest_name=g['guest_name'].strip(),
                customer_type_id=int(g['customer_type_id']),
                identity_card=g.get('identity_card', '').strip(),
                address=g.get('address', '').strip()
            )
            db.session.add(rg)

        room.status = 'DANG_THUE'

    if booking:
        booking.status = 'DA_NHAN'

    db.session.commit()
    return rental


def load_active_rentals():
    return Rental.query.filter_by(status='DANG_THUE').order_by(Rental.id.desc()).all()


def load_invoices():
    return Invoice.query.order_by(Invoice.id.desc()).all()


def calculate_rental_bill(rental_id, actual_checkout=None):
    rental = Rental.query.get(int(rental_id))
    if not rental:
        return None

    checkout = actual_checkout if actual_checkout else rental.checkout_date
    days = (checkout - rental.checkin_date).days
    if days <= 0:
        days = 1

    items = []
    total_amount = 0.0
    rep_customer = "Khach hang"
    room_names = []

    for idx, d in enumerate(rental.details):
        if idx == 0 and d.guests:
            rep_customer = d.guests[0].guest_name
        room_names.append(d.room.name)
        guest_count = len(d.guests)
        amount = round(days * d.unit_price * (1.0 + d.surcharge_rate) * d.customer_coefficient)
        total_amount += amount
        items.append({
            'room_name': d.room.name,
            'room_type': d.room.room_type.name,
            'unit_price': d.unit_price,
            'days': days,
            'guest_count': guest_count,
            'surcharge_pct': int(round(d.surcharge_rate * 100)),
            'coefficient': d.customer_coefficient,
            'amount': amount
        })

    return {
        'rental': rental,
        'customer_name': rep_customer,
        'rooms_summary': ', '.join(room_names),
        'checkin_date': rental.checkin_date,
        'checkout_date': checkout,
        'days': days,
        'items': items,
        'total_amount': total_amount
    }


def pay_rental(rental_id, actual_checkout=None, staff_id=None):
    bill = calculate_rental_bill(rental_id, actual_checkout)
    if not bill:
        raise ValueError("Khong tim thay phieu thue phong.")

    rental = bill['rental']
    if rental.status == 'DA_THANH_TOAN':
        raise ValueError("Phieu thue nay da duoc thanh toan.")

    rental.checkout_date = bill['checkout_date']
    rental.status = 'DA_THANH_TOAN'

    for d in rental.details:
        d.room.status = 'TRONG'

    invoice = Invoice(
        rental_id=rental.id,
        customer_name=bill['customer_name'],
        rooms_summary=bill['rooms_summary'],
        checkin_date=bill['checkin_date'],
        checkout_date=bill['checkout_date'],
        payment_date=date.today(),
        total_amount=bill['total_amount'],
        staff_id=staff_id
    )
    db.session.add(invoice)
    db.session.commit()
    return invoice


def stats_revenue_by_month(month, year):
    room_types = RoomType.query.all()
    invoices = Invoice.query.filter(
        extract('month', Invoice.payment_date) == int(month),
        extract('year', Invoice.payment_date) == int(year)
    ).all()

    rev_map = {rt.id: {'name': rt.name, 'revenue': 0.0, 'count': 0} for rt in room_types}
    total_revenue = 0.0

    for inv in invoices:
        rental = inv.rental
        days = (inv.checkout_date - inv.checkin_date).days
        if days <= 0:
            days = 1
        for d in rental.details:
            rt_id = d.room.room_type_id
            amount = round(days * d.unit_price * (1.0 + d.surcharge_rate) * d.customer_coefficient)
            if rt_id in rev_map:
                rev_map[rt_id]['revenue'] += amount
                rev_map[rt_id]['count'] += 1
                total_revenue += amount

    rows = []
    for data in rev_map.values():
        ratio = round((data['revenue'] / total_revenue) * 100, 1) if total_revenue > 0 else 0.0
        rows.append({
            'room_type': data['name'],
            'revenue': data['revenue'],
            'count': data['count'],
            'ratio': ratio
        })

    return rows, total_revenue


def stats_room_density_by_month(month, year):
    days_in_month = calendar.monthrange(int(year), int(month))[1]
    rooms = Room.query.order_by(Room.name).all()
    rentals = Rental.query.filter(
        extract('month', Rental.checkin_date) == int(month),
        extract('year', Rental.checkin_date) == int(year)
    ).all()

    days_map = {r.id: 0 for r in rooms}
    for rt in rentals:
        d_count = (rt.checkout_date - rt.checkin_date).days
        if d_count <= 0:
            d_count = 1
        for d in rt.details:
            if d.room_id in days_map:
                days_map[d.room_id] += d_count

    rows = []
    for r in rooms:
        rented_days = days_map[r.id]
        ratio = round((rented_days / days_in_month) * 100, 1) if days_in_month > 0 else 0.0
        rows.append({
            'room_name': r.name,
            'rented_days': rented_days,
            'ratio': ratio
        })

    return rows, days_in_month
