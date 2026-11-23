from datetime import date, timedelta
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash
from hotelapp import db, app


class User(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role = Column(String(20), default='CUSTOMER')
    active = Column(Boolean, default=True)

    def __str__(self):
        return self.name


class Regulation(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    max_guests_per_room = Column(Integer, default=3, nullable=False)
    standard_guests = Column(Integer, default=2, nullable=False)
    surcharge_rate = Column(Float, default=0.25, nullable=False)
    max_advance_days = Column(Integer, default=28, nullable=False)

    def __str__(self):
        return f"Max {self.max_guests_per_room} guests - Surcharge {int(self.surcharge_rate * 100)}%"


class RoomType(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    price = Column(Float, default=0, nullable=False)
    rooms = relationship('Room', backref='room_type', lazy=True)

    def __str__(self):
        return f"{self.name} ({int(self.price):,} VND)"


class CustomerType(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    coefficient = Column(Float, default=1.0, nullable=False)

    def __str__(self):
        return f"{self.name} (x{self.coefficient})"


class Room(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    status = Column(String(30), default='TRONG', nullable=False)
    image = Column(String(255), default='https://images.unsplash.com/photo-1566665797739-1674de7a421a?w=600')
    room_type_id = Column(Integer, ForeignKey(RoomType.id), nullable=False)

    @property
    def price(self):
        return self.room_type.price if self.room_type else 0

    def __str__(self):
        return self.name


class Booking(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    booker_name = Column(String(100), nullable=False)
    booking_date = Column(Date, default=date.today, nullable=False)
    checkin_date = Column(Date, nullable=False)
    checkout_date = Column(Date, nullable=False)
    status = Column(String(30), default='CHO_NHAN', nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=True)
    details = relationship('BookingDetail', backref='booking', cascade='all, delete-orphan', lazy=True)

    def __str__(self):
        return f"DP#{self.id} - {self.booker_name}"


class BookingDetail(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey(Booking.id), nullable=False)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)
    room = relationship('Room', lazy=True)
    guests = relationship('BookingGuest', backref='booking_detail', cascade='all, delete-orphan', lazy=True)


class BookingGuest(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_detail_id = Column(Integer, ForeignKey(BookingDetail.id), nullable=False)
    guest_name = Column(String(100), nullable=False)
    customer_type_id = Column(Integer, ForeignKey(CustomerType.id), nullable=False)
    identity_card = Column(String(50), nullable=True)
    address = Column(String(200), nullable=True)
    customer_type = relationship('CustomerType', lazy=True)


class Rental(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(Integer, ForeignKey(Booking.id), nullable=True)
    staff_id = Column(Integer, ForeignKey(User.id), nullable=True)
    checkin_date = Column(Date, nullable=False)
    checkout_date = Column(Date, nullable=False)
    status = Column(String(30), default='DANG_THUE', nullable=False)
    details = relationship('RentalDetail', backref='rental', cascade='all, delete-orphan', lazy=True)

    def __str__(self):
        return f"PT#{self.id}"


class RentalDetail(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    rental_id = Column(Integer, ForeignKey(Rental.id), nullable=False)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)
    unit_price = Column(Float, default=0, nullable=False)
    surcharge_rate = Column(Float, default=0, nullable=False)
    customer_coefficient = Column(Float, default=1.0, nullable=False)
    room = relationship('Room', lazy=True)
    guests = relationship('RentalGuest', backref='rental_detail', cascade='all, delete-orphan', lazy=True)


class RentalGuest(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    rental_detail_id = Column(Integer, ForeignKey(RentalDetail.id), nullable=False)
    guest_name = Column(String(100), nullable=False)
    customer_type_id = Column(Integer, ForeignKey(CustomerType.id), nullable=False)
    identity_card = Column(String(50), nullable=True)
    address = Column(String(200), nullable=True)
    customer_type = relationship('CustomerType', lazy=True)


class Invoice(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    rental_id = Column(Integer, ForeignKey(Rental.id), nullable=False)
    customer_name = Column(String(100), nullable=False)
    rooms_summary = Column(String(200), nullable=False)
    checkin_date = Column(Date, nullable=False)
    checkout_date = Column(Date, nullable=False)
    payment_date = Column(Date, default=date.today, nullable=False)
    total_amount = Column(Float, default=0, nullable=False)
    staff_id = Column(Integer, ForeignKey(User.id), nullable=True)
    rental = relationship('Rental', lazy=True)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not Regulation.query.first():
            reg = Regulation(max_guests_per_room=3, standard_guests=2, surcharge_rate=0.25, max_advance_days=28)
            db.session.add(reg)

        if not User.query.first():
            users = [
                User(name='Quan Tri Vien', username='admin', password=generate_password_hash('123456'), role='ADMIN'),
                User(name='Nhan Vien Le Tan', username='staff', password=generate_password_hash('123456'), role='STAFF'),
                User(name='Tran Phuong Kien', username='kien', password=generate_password_hash('123456'), role='CUSTOMER')
            ]
            db.session.add_all(users)

        if not RoomType.query.first():
            rt1 = RoomType(name='Loai A', price=150000)
            rt2 = RoomType(name='Loai B', price=170000)
            rt3 = RoomType(name='Loai C', price=200000)
            db.session.add_all([rt1, rt2, rt3])
            db.session.commit()

        if not CustomerType.query.first():
            ct1 = CustomerType(name='Noi dia', coefficient=1.0)
            ct2 = CustomerType(name='Nuoc ngoai', coefficient=1.5)
            db.session.add_all([ct1, ct2])
            db.session.commit()

        if not Room.query.first():
            rooms = [
                Room(name='P101', room_type_id=1, status='TRONG', image='https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=600'),
                Room(name='P102', room_type_id=1, status='DANG_THUE', image='https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=600'),
                Room(name='P103', room_type_id=2, status='DA_DAT', image='https://images.unsplash.com/photo-1590490360182-c33d57733427?w=600'),
                Room(name='P201', room_type_id=2, status='TRONG', image='https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=600'),
                Room(name='P202', room_type_id=3, status='TRONG', image='https://images.unsplash.com/photo-1578683010236-d716f9a3f461?w=600'),
                Room(name='P203', room_type_id=3, status='TRONG', image='https://images.unsplash.com/photo-1566665797739-1674de7a421a?w=600')
            ]
            db.session.add_all(rooms)
            db.session.commit()

        if not Booking.query.first():
            today = date.today()
            bk = Booking(
                booker_name='Nguyen Minh Quan',
                booking_date=today,
                checkin_date=today + timedelta(days=2),
                checkout_date=today + timedelta(days=5),
                status='CHO_NHAN'
            )
            db.session.add(bk)
            db.session.flush()
            bd = BookingDetail(booking_id=bk.id, room_id=3)
            db.session.add(bd)
            db.session.flush()
            db.session.add_all([
                BookingGuest(booking_detail_id=bd.id, guest_name='Nguyen Minh Quan', customer_type_id=1, identity_card='079204001122', address='Thu Duc, TP.HCM'),
                BookingGuest(booking_detail_id=bd.id, guest_name='Le Thu Ha', customer_type_id=1, identity_card='079304005566', address='Quan 1, TP.HCM')
            ])

            rt_active = Rental(
                checkin_date=today - timedelta(days=1),
                checkout_date=today + timedelta(days=2),
                status='DANG_THUE'
            )
            db.session.add(rt_active)
            db.session.flush()
            rd_active = RentalDetail(rental_id=rt_active.id, room_id=2, unit_price=150000, surcharge_rate=0.25, customer_coefficient=1.5)
            db.session.add(rd_active)
            db.session.flush()
            db.session.add_all([
                RentalGuest(rental_detail_id=rd_active.id, guest_name='Dang Quoc Huy', customer_type_id=1, identity_card='079200003344', address='Thu Duc, TP.HCM'),
                RentalGuest(rental_detail_id=rd_active.id, guest_name='Kenji Sato', customer_type_id=2, identity_card='JP9920145', address='Tokyo, Japan'),
                RentalGuest(rental_detail_id=rd_active.id, guest_name='Bui Thanh Tung', customer_type_id=1, identity_card='079201007788', address='Nha Be, TP.HCM')
            ])

            rt_paid = Rental(
                checkin_date=today - timedelta(days=4),
                checkout_date=today - timedelta(days=1),
                status='DA_THANH_TOAN'
            )
            db.session.add(rt_paid)
            db.session.flush()
            rd_paid = RentalDetail(rental_id=rt_paid.id, room_id=5, unit_price=200000, surcharge_rate=0.0, customer_coefficient=1.5)
            db.session.add(rd_paid)
            db.session.flush()
            db.session.add_all([
                RentalGuest(rental_detail_id=rd_paid.id, guest_name='David Miller', customer_type_id=2, identity_card='P88492011', address='California, USA'),
                RentalGuest(rental_detail_id=rd_paid.id, guest_name='Vo Hoang Yen', customer_type_id=1, identity_card='079199008811', address='Quan 7, TP.HCM')
            ])
            inv = Invoice(
                rental_id=rt_paid.id,
                customer_name='David Miller',
                rooms_summary='P202',
                checkin_date=rt_paid.checkin_date,
                checkout_date=rt_paid.checkout_date,
                payment_date=rt_paid.checkout_date,
                total_amount=900000
            )
            db.session.add(inv)
            db.session.commit()
