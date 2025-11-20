from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def generate_receipt_pdf(payment, student, fee, admin):
    # Create PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # School header
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(300, 750, "School Fee Receipt")
    
    # Student details
    p.setFont("Helvetica", 12)
    p.drawString(50, 700, f"Receipt No: {payment.receipt_number}")
    p.drawString(50, 680, f"Date: {payment.payment_date.strftime('%d-%m-%Y')}")
    p.drawString(50, 660, f"Student Name: {student.name}")
    p.drawString(50, 640, f"Roll Number: {student.roll_number}")
    p.drawString(50, 620, f"Class: {student.class_name}")
    
    # Fee details
    p.drawString(50, 580, "Fee Details:")
    p.drawString(70, 560, f"Base Fee: ₹{fee.base_fee}")
    if fee.hostel_food_fee:
        p.drawString(70, 540, f"Hostel+Food Fee: ₹{fee.hostel_food_fee}")
    if fee.milk_fee:
        p.drawString(70, 520, f"Milk Fee: ₹{fee.milk_fee}")
    if fee.discount:
        p.drawString(70, 500, f"Discount: ₹{fee.discount}")
    p.drawString(50, 460, f"Total Fee: ₹{fee.total_fee}")
    p.drawString(50, 440, f"Amount Paid: ₹{payment.amount}")
    p.drawString(50, 420, f"Balance: ₹{fee.total_fee - fee.paid_amount}")
    p.drawString(50, 400, f"Payment Method: {payment.payment_method.upper()}")
    if payment.transaction_id:
        p.drawString(50, 380, f"Transaction ID: {payment.transaction_id}")
    
    # Signature
    p.drawString(50, 320, "Received by:")
    p.drawString(50, 300, admin.username)
    
    p.showPage()
    p.save()
    
    return buffer