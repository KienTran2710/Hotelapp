from flask import session, redirect
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from wtforms import FloatField
from hotelapp import app, db
from hotelapp.models import RoomType, CustomerType, Regulation, Room, User


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return redirect('/')
class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return session.get('role') == 'ADMIN'

    def inaccessible_callback(self, name, **kwargs):
        return redirect('/login')


class RoomTypeView(AuthenticatedModelView):
    column_list = ['id', 'name', 'price']
    column_labels = {'id': 'Ma loai', 'name': 'Ten loai phong', 'price': 'Don gia (VND)'}
    can_export = True
    column_searchable_list = ['name']
    column_filters = ['name', 'price']
    edit_modal = True
    column_editable_list = ['name', 'price']
    form_overrides = {'price': FloatField}


class CustomerTypeView(AuthenticatedModelView):
    column_list = ['id', 'name', 'coefficient']
    column_labels = {'id': 'Ma loai', 'name': 'Loai khach', 'coefficient': 'He so'}
    edit_modal = True
    column_editable_list = ['name', 'coefficient']
    form_overrides = {'coefficient': FloatField}


class RegulationView(AuthenticatedModelView):
    column_list = ['id', 'max_guests_per_room', 'standard_guests', 'surcharge_rate', 'max_advance_days']
    column_labels = {
        'id': 'ID',
        'max_guests_per_room': 'So khach toi da / phong',
        'standard_guests': 'So khach tieu chuan',
        'surcharge_rate': 'Ty le phu thu (0.25 = 25%)',
        'max_advance_days': 'Han dat truoc toi da (ngay)'
    }
    can_create = False
    can_delete = False
    edit_modal = True
    column_editable_list = ['max_guests_per_room', 'standard_guests', 'surcharge_rate', 'max_advance_days']
    form_overrides = {'surcharge_rate': FloatField}


class RoomView(AuthenticatedModelView):
    column_list = ['id', 'name', 'room_type', 'status']
    column_labels = {'id': 'ID', 'name': 'Phong', 'room_type': 'Loai phong', 'status': 'Tinh trang'}
    can_export = True
    column_searchable_list = ['name', 'status']
    column_filters = ['name', 'status', 'room_type_id']
    edit_modal = True
    column_editable_list = ['name', 'status']
    can_view_details = True
    details_modal = True


class UserView(AuthenticatedModelView):
    column_list = ['id', 'name', 'username', 'role', 'active']
    column_searchable_list = ['name', 'username']
    column_filters = ['role', 'active']


class StatsRedirectView(BaseView):
    @expose('/')
    def index(self):
        return redirect('/stats')


admin = Admin(app=app, name='Hotel Management Admin', index_view=MyAdminIndexView())
admin.add_view(RoomView(Room, db.session, name='Danh sách phòng'))
admin.add_view(RoomTypeView(RoomType, db.session, name='Loai phong & Don gia'))
admin.add_view(CustomerTypeView(CustomerType, db.session, name='Loai khach & He so'))
admin.add_view(RegulationView(Regulation, db.session, name='Thay doi quy dinh'))
admin.add_view(UserView(User, db.session, name='Tai khoan'))
admin.add_view(StatsRedirectView(name='Bao cao & Bieu do', endpoint='admin_stats'))