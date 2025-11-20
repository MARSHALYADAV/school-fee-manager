from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from application.models import Admin, AuditLog
from application import db
from datetime import datetime

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.objects(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            
            # Update last login time
            admin.last_login = datetime.utcnow()
            admin.save()
            
            # Create audit log
            log = AuditLog(
                admin=admin,
                action='LOGIN',
                details=f'Admin {admin.username} logged in'
            )
            log.save()
            
            return redirect(url_for('admin.dashboard'))
        
        flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    # Create audit log before logout
    log = AuditLog(
        admin=current_user.id,
        action='LOGOUT',
        details=f'Admin {current_user.username} logged out'
    )
    log.save()
    
    logout_user()
    return redirect(url_for('auth.login'))