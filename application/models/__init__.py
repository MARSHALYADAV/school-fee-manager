from application import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Admin(UserMixin, db.Document):
    username = db.StringField(max_length=64, unique=True, required=True)
    email = db.StringField(max_length=120, unique=True, required=True)
    password_hash = db.StringField(max_length=128)
    created_at = db.DateTimeField(default=datetime.utcnow)
    last_login = db.DateTimeField()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Flask-Login requires get_id to return a string
    def get_id(self):
        return str(self.id)

class Student(db.Document):
    name = db.StringField(max_length=100, required=True)
    roll_number = db.StringField(max_length=20, unique=True, required=True)
    class_name = db.StringField(max_length=10, required=True)
    section = db.StringField(max_length=5, required=True)
    contact = db.StringField(max_length=15, required=True)
    economic_status = db.StringField(max_length=10, required=True)  # Normal/Poor
    hostel_food_opted = db.BooleanField(default=False)
    milk_opted = db.BooleanField(default=False)
    created_at = db.DateTimeField(default=datetime.utcnow)
    updated_at = db.DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super(Student, self).save(*args, **kwargs)

class Fee(db.Document):
    student = db.ReferenceField('Student', required=True)
    month = db.StringField(max_length=10, required=True)
    year = db.StringField(max_length=10, required=True)
    base_fee = db.FloatField(required=True)
    hostel_food_fee = db.FloatField(default=0.0)
    milk_fee = db.FloatField(default=0.0)
    discount = db.FloatField(default=0.0)
    total_fee = db.FloatField(required=True)
    paid_amount = db.FloatField(default=0.0)
    created_at = db.DateTimeField(default=datetime.utcnow)
    updated_at = db.DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super(Fee, self).save(*args, **kwargs)

class PaymentHistory(db.Document):
    student = db.ReferenceField('Student', required=True)
    fee = db.ReferenceField('Fee', required=True)
    amount = db.FloatField(required=True)
    payment_date = db.DateTimeField(default=datetime.utcnow)
    receipt_number = db.StringField(max_length=20, unique=True, required=True)
    created_by = db.ReferenceField('Admin', required=True)
    payment_method = db.StringField(max_length=10, default='cash')
    transaction_id = db.StringField(max_length=64)

class AuditLog(db.Document):
    admin = db.ReferenceField('Admin', required=True)
    action = db.StringField(max_length=100, required=True)
    details = db.StringField()
    timestamp = db.DateTimeField(default=datetime.utcnow)