
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Student, Fee, Admin, AuditLog
from app import db
from datetime import datetime
import pytz

bp = Blueprint('admin', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    total_students = Student.objects.count()
    total_hostelers = Student.objects(hostel_food_opted=True).count()
    total_food = Student.objects(hostel_food_opted=True).count()
    poor_students = Student.objects(economic_status='Poor').count()
    
    # Fee statistics for current year
    current_year = str(datetime.now().year)
    
    # MongoEngine aggregation for sums
    pipeline = [
        {'$match': {'year': current_year}},
        {'$group': {
            '_id': None, 
            'total_fees': {'$sum': '$total_fee'},
            'collected_fees': {'$sum': '$paid_amount'}
        }}
    ]
    
    fee_stats = list(Fee.objects.aggregate(pipeline))
    if fee_stats:
        total_fees = fee_stats[0]['total_fees']
        collected_fees = fee_stats[0]['collected_fees']
    else:
        total_fees = 0
        collected_fees = 0
        
    pending_fees = total_fees - collected_fees
    
    # Get class-wise student count
    class_pipeline = [
        {'$group': {
            '_id': '$class_name',
            'count': {'$sum': 1}
        }}
    ]
    class_stats = list(Student.objects.aggregate(class_pipeline))
    # Format for template: [(class_name, count), ...]
    class_distribution = [(stat['_id'], stat['count']) for stat in class_stats]
    # Sort by class name (simple string sort for now)
    class_distribution.sort(key=lambda x: x[0])
    
    # Get recent audit logs
    recent_logs = AuditLog.objects.order_by('-timestamp').limit(10)
    local_tz = pytz.timezone('Asia/Kolkata')
    
    # We need to convert to list to modify attributes or use a wrapper
    # But MongoEngine documents are mutable, so we can just iterate
    # However, adding a new attribute 'local_timestamp' to the document object might not persist or might be cleaner to do in template or view model
    # Let's just pass the logs and handle TZ in template or here
    logs_to_display = []
    for log in recent_logs:
        # Create a simple object or dict to hold display data
        log_data = {
            'action': log.action,
            'details': log.details,
            'admin': log.admin,
            'timestamp': log.timestamp,
            'local_timestamp': log.timestamp.replace(tzinfo=pytz.utc).astimezone(local_tz) if log.timestamp else None
        }
        logs_to_display.append(log_data)
    
    # Get other active admins
    active_admins = Admin.objects(last_login__exists=True).order_by('-last_login')
    
    return render_template('admin/dashboard.html',
                         total_students=total_students,
                         total_hostelers=total_hostelers,
                         total_food=total_food,
                         poor_students=poor_students,
                         total_fees=total_fees,
                         collected_fees=collected_fees,
                         pending_fees=pending_fees,
                         class_distribution=class_distribution,
                         recent_logs=logs_to_display,
                         active_admins=active_admins)