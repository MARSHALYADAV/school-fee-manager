from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from application.models import Student, AuditLog, Fee, PaymentHistory
from application import db
from datetime import datetime

bp = Blueprint('student', __name__, url_prefix='/student')

@bp.route('/')
@login_required
def list_students():
    # Get filter parameters
    class_filter = request.args.get('class')
    hostel_food_filter = request.args.get('hostel_food')
    milk_filter = request.args.get('milk')
    economic_filter = request.args.get('economic')
    
    # Base query
    query = Student.objects
    
    # Apply filters
    if class_filter:
        query = query.filter(class_name=class_filter)
    if hostel_food_filter:
        query = query.filter(hostel_food_opted=(hostel_food_filter == 'yes'))
    if milk_filter:
        query = query.filter(milk_opted=(milk_filter == 'yes'))
    if economic_filter:
        query = query.filter(economic_status=economic_filter)
    
    students = query.all()
    return render_template('student/list.html', students=students)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        try:
            student = Student(
                name=request.form['name'],
                roll_number=request.form['roll_number'],
                class_name=request.form['class_name'],
                section=request.form['section'],
                contact=request.form['contact'],
                economic_status=request.form['economic_status'],
                hostel_food_opted=bool(request.form.get('hostel_food_opted')),
                milk_opted=bool(request.form.get('milk_opted'))
            )
            
            student.save()
            
            # Create audit log
            log = AuditLog(
                admin=current_user.id,
                action='CREATE_STUDENT',
                details=f'Created student {student.name} (Roll: {student.roll_number})'
            )
            log.save()
            
            flash('Student added successfully!', 'success')
            return redirect(url_for('student.list_students'))
            
        except Exception as e:
            flash(f'Error adding student: {str(e)}', 'error')
    
    return render_template('student/add.html')

@bp.route('/edit/<string:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = Student.objects.get_or_404(pk=id)
    
    if request.method == 'POST':
        try:
            old_data = {
                'name': student.name,
                'roll_number': student.roll_number,
                'class_name': student.class_name,
                'section': student.section,
                'contact': student.contact,
                'economic_status': student.economic_status,
                'hostel_food_opted': student.hostel_food_opted,
                'milk_opted': student.milk_opted
            }
            
            student.name = request.form['name']
            student.roll_number = request.form['roll_number']
            student.class_name = request.form['class_name']
            student.section = request.form['section']
            student.contact = request.form['contact']
            student.economic_status = request.form['economic_status']
            student.hostel_food_opted = bool(request.form.get('hostel_food_opted'))
            student.milk_opted = bool(request.form.get('milk_opted'))
            student.updated_at = datetime.utcnow()
            
            # Create audit log
            changes = []
            for key, old_value in old_data.items():
                new_value = getattr(student, key)
                if old_value != new_value:
                    changes.append(f"{key}: {old_value} → {new_value}")
            
            if changes:
                log = AuditLog(
                    admin=current_user.id,
                    action='EDIT_STUDENT',
                    details=f'Updated student {student.name} (Roll: {student.roll_number})\nChanges:\n' + '\n'.join(changes)
                )
                log.save()
            
            student.save()
            flash('Student updated successfully!', 'success')
            return redirect(url_for('student.list_students'))
            
        except Exception as e:
            flash(f'Error updating student: {str(e)}', 'error')
    
    return render_template('student/edit.html', student=student)

@bp.route('/delete/<string:id>', methods=['POST'])
@login_required
def delete_student(id):
    student = Student.objects.get_or_404(pk=id)
    try:
        # Create audit log before deletion
        log = AuditLog(
            admin=current_user.id,
            action='DELETE_STUDENT',
            details=f'Deleted student {student.name} (Roll: {student.roll_number})'
        )
        log.save()

        # Delete related payments and fees
        # In MongoEngine, if we set reverse_delete_rule=CASCADE in models, this happens automatically.
        # But since we didn't set it explicitly yet, we can do manual deletion or rely on the fact that ReferenceField doesn't enforce FK constraints strictly like SQL.
        # Ideally, we should delete them.
        Fee.objects(student=student).delete()
        PaymentHistory.objects(student=student).delete()

        student.delete()
        flash('Student deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting student: {str(e)}', 'error')
    return redirect(url_for('student.list_students'))