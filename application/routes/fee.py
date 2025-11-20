from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, make_response
from flask_login import login_required, current_user
from application.models import Student, Fee, PaymentHistory, AuditLog
from application import db
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import json
from application.utils import generate_receipt_pdf

bp = Blueprint('fee', __name__, url_prefix='/fee')

# ...existing code...

# Add the new routes here
@bp.route('/get/<string:fee_id>')
@login_required
def get_fee(fee_id):
    fee = Fee.objects.get_or_404(pk=fee_id)
    return jsonify({
        'month': fee.month,
        'year': fee.year,
        'base_fee': fee.base_fee,
        'hostel_food_fee': fee.hostel_food_fee,
        'milk_fee': fee.milk_fee,
        'discount': fee.discount
    })

@bp.route('/edit/<string:fee_id>', methods=['POST'])
@login_required
def edit_fee(fee_id):
    fee = Fee.objects.get_or_404(pk=fee_id)
    try:
        old_data = {
            'month': fee.month,
            'year': fee.year,
            'base_fee': fee.base_fee,
            'hostel_food_fee': fee.hostel_food_fee,
            'milk_fee': fee.milk_fee,
            'discount': fee.discount,
            'total_fee': fee.total_fee
        }
        fee.month = request.form['month']
        fee.year = request.form['year']
        fee.base_fee = float(request.form['base_fee'])
        fee.hostel_food_fee = float(request.form['hostel_food_fee'])
        fee.milk_fee = float(request.form['milk_fee'])
        fee.discount = float(request.form['discount'])
        fee.total_fee = fee.base_fee + fee.hostel_food_fee + fee.milk_fee - fee.discount
        fee.updated_at = datetime.utcnow()

        # Audit log for changes
        changes = []
        for key, old_value in old_data.items():
            new_value = getattr(fee, key)
            if old_value != new_value:
                changes.append(f"{key}: {old_value}   {new_value}")
        if changes:
            student = fee.student
            log = AuditLog(
                admin=current_user.id,
                action='EDIT_FEE',
                details=f'Edited fee for student {student.name} (Roll: {student.roll_number})\nChanges:\n' + '\n'.join(changes)
            )
            log.save()

        fee.save()
        flash('Fee updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating fee: {str(e)}', 'error')
    return redirect(url_for('fee.manage_fees'))
 
class_fee_structure = {
    '1': {'base': 5000, 'hostel': 20000, 'food': 15000},
    '2': {'base': 5500, 'hostel': 20000, 'food': 15000},
    '3': {'base': 6000, 'hostel': 20000, 'food': 15000},
    '4': {'base': 6500, 'hostel': 20000, 'food': 15000},
    '5': {'base': 7000, 'hostel': 20000, 'food': 15000},
    '6': {'base': 7500, 'hostel': 20000, 'food': 15000},
    '7': {'base': 8000, 'hostel': 20000, 'food': 15000},
    '8': {'base': 8500, 'hostel': 20000, 'food': 15000},
    '9': {'base': 9000, 'hostel': 20000, 'food': 15000},
    '10': {'base': 9500, 'hostel': 20000, 'food': 15000},
}

@bp.route('/')
@login_required
def manage_fees():
    # Get filter parameters
    status = request.args.get('status')
    class_filter = request.args.get('class')
    
    # Base query parameters
    month = request.args.get('month') or str(datetime.now().month)
    year = request.args.get('year') or str(datetime.now().year)
    
    # In MongoDB, we can't easily do a left outer join in one query like SQL.
    # Strategy:
    # 1. Fetch all students (filtered by class if needed).
    # 2. Fetch all fees for the given month/year.
    # 3. Map fees to students in Python.
    
    # 1. Fetch Students
    student_query = Student.objects
    if class_filter:
        student_query = student_query.filter(class_name=class_filter)
    students = list(student_query.all())
    
    # 2. Fetch Fees
    # We want fees for these students for the specific month/year
    student_ids = [s.id for s in students]
    fees = Fee.objects(student__in=student_ids, month=month, year=year)
    fee_map = {f.student.id: f for f in fees}
    
    # 3. Combine
    students_fees = []
    for student in students:
        fee = fee_map.get(student.id)
        
        # Apply status filter in Python
        include = True
        if status:
            if status == 'fully_paid':
                if not fee or fee.paid_amount < fee.total_fee:
                    include = False
            elif status == 'pending':
                if fee and fee.paid_amount >= fee.total_fee:
                    include = False
                # If fee is None, it's pending (not even created), so include it
            elif status == 'discounted':
                if not fee or fee.discount <= 0:
                    include = False
        
        if include:
            # Emulate the SQL result tuple (Student, Fee)
            students_fees.append((student, fee))
            
    return render_template('fee/manage.html', students_fees=students_fees, class_fee_structure=class_fee_structure, now=datetime.now())

@bp.route('/calculate/<string:student_id>')
@login_required
def calculate_fee(student_id):
    student = Student.objects.get_or_404(pk=student_id)
    fees = class_fee_structure.get(student.class_name, {})
    base_fee = fees.get('base', 0)
    hostel_food_fee = fees.get('hostel', 0) if student.hostel_food_opted else 0
    milk_fee = 500 if student.milk_opted else 0
    total = base_fee + hostel_food_fee + milk_fee
    return jsonify({
        'base_fee': base_fee,
        'hostel_food_fee': hostel_food_fee,
        'milk_fee': milk_fee,
        'total': total
    })

@bp.route('/add/<string:student_id>', methods=['POST'])
@login_required
def add_fee(student_id):
    student = Student.objects.get_or_404(pk=student_id)
    month = request.form.get('month', str(datetime.now().month))
    year = request.form.get('year', str(datetime.now().year))
    # Check if fee record already exists
    existing_fee = Fee.objects(
        student=student,
        month=month,
        year=year
    ).first()
    if existing_fee:
        flash('Fee record already exists for this month and year', 'error')
        return redirect(url_for('fee.manage_fees'))
    try:
        fee = Fee(
            student=student,
            month=month,
            year=year,
            base_fee=float(request.form['base_fee']),
            hostel_food_fee=float(request.form['hostel_food_fee']),
            milk_fee=float(request.form['milk_fee']),
            discount=float(request.form.get('discount', 0)),
        )
        # Calculate total fee
        fee.total_fee = fee.base_fee + fee.hostel_food_fee + fee.milk_fee - fee.discount
        fee.save()
        
        # Create audit log
        log = AuditLog(
            admin=current_user.id,
            action='ADD_FEE',
            details=f'Added fee for student {student.name} (Roll: {student.roll_number})\n' + \
                    f'Base: {fee.base_fee}, Hostel+Food: {fee.hostel_food_fee}, Milk: {fee.milk_fee}\n' + \
                    f'Discount: {fee.discount}, Total: {fee.total_fee}'
        )
        log.save()
        flash('Fee added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding fee: {str(e)}', 'error')
    return redirect(url_for('fee.manage_fees'))

@bp.route('/payment/<string:fee_id>', methods=['POST'])
@login_required
def add_payment(fee_id):
    fee = Fee.objects.get_or_404(pk=fee_id)
    amount = float(request.form['amount'])
    payment_method = request.form.get('payment_method', 'cash')
    transaction_id = request.form.get('transaction_id') if payment_method == 'qr' else None
    want_json = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    try:
        if amount <= 0:
            raise ValueError("Payment amount must be greater than 0")

        remaining = fee.total_fee - fee.paid_amount
        if amount > remaining:
            raise ValueError(f"Payment amount exceeds remaining fee ({remaining})")

        # Create payment record
        payment = PaymentHistory(
            student=fee.student,
            fee=fee,
            amount=amount,
            receipt_number=f"RCP{datetime.now().strftime('%Y%m%d%H%M%S')}",
            created_by=current_user.id,
            payment_method=payment_method,
            transaction_id=transaction_id
        )

        # Update fee paid amount
        fee.paid_amount += amount

        payment.save()
        fee.save()

        # Create audit log
        student = fee.student
        log = AuditLog(
            admin=current_user.id,
            action='ADD_PAYMENT',
            details=f'Added payment for student {student.name} (Roll: {student.roll_number})\n' + \
                    f'Amount: {amount}, Receipt: {payment.receipt_number}, Method: {payment_method}' + \
                    (f', Txn: {transaction_id}' if transaction_id else '')
        )
        log.save()

        flash('Payment recorded successfully!', 'success')

        # Generate receipt PDF using utility
        # student and fee are available in this scope
        buffer = generate_receipt_pdf(payment, student, fee, current_user)

        if want_json:
            return jsonify({
                'success': True,
                'message': 'Payment recorded successfully!',
                'receipt_url': url_for('fee.generate_receipt', payment_id=str(payment.id))
            })
        else:
            # Return PDF directly
            buffer.seek(0)
            response = make_response(buffer.getvalue())
            response.mimetype = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename=receipt_{payment.receipt_number}.pdf'
            return response

    except Exception as e:
        flash(f'Error recording payment: {str(e)}', 'error')
        if want_json:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        else:
            return redirect(url_for('fee.manage_fees'))

@bp.route('/receipt/<string:payment_id>')
@login_required
def generate_receipt(payment_id):
    payment = PaymentHistory.objects.get_or_404(pk=payment_id)
    student = payment.student
    fee = payment.fee
    admin = current_user
    
    # Create PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # School header
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(300, 750, "School Fee Receipt")
    
    # Fee details
    p.drawString(50, 540, "Fee Details:")
    p.drawString(70, 520, f"Base Fee:  {fee.base_fee}")
    if fee.hostel_food_fee:
        p.drawString(70, 500, f"Hostel+Food Fee:  {fee.hostel_food_fee}")
    if fee.milk_fee:
        p.drawString(70, 480, f"Milk Fee:  {fee.milk_fee}")
    if fee.discount:
        p.drawString(70, 460, f"Discount:  {fee.discount}")
    p.drawString(50, 420, f"Total Fee:  {fee.total_fee}")
    p.drawString(50, 400, f"Amount Paid:  {payment.amount}")
    p.drawString(50, 380, f"Balance:  {fee.total_fee - fee.paid_amount}")
    p.drawString(50, 360, f"Payment Method: {payment.payment_method}")
    if payment.transaction_id:
        p.drawString(50, 340, f"Transaction ID: {payment.transaction_id}")
    # Signature
    p.drawString(50, 300, "Received by:")
    p.drawString(50, 280, admin.username)
    if fee.milk_fee:
        p.drawString(70, 480, f"Milk Fee: ₹{fee.milk_fee}")
    if fee.discount:
        p.drawString(70, 460, f"Discount: ₹{fee.discount}")
    p.drawString(50, 420, f"Total Fee: ₹{fee.total_fee}")
    p.drawString(50, 400, f"Amount Paid: ₹{payment.amount}")
    p.drawString(50, 380, f"Balance: ₹{fee.total_fee - fee.paid_amount}")
    
    # Signature
    p.drawString(50, 300, "Received by:")
    p.drawString(50, 280, admin.username)
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.mimetype = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=receipt_{payment.receipt_number}.pdf'
    
    return response