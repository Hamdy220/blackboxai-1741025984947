from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import os
import arabic_reshaper
from bidi.algorithm import get_display
from datetime import datetime

class InvoiceGenerator:
    def __init__(self, database):
        self.database = database
        
        # تحميل الخط العربي
        font_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts', 'Cairo-Regular.ttf')
        pdfmetrics.registerFont(TTFont('Arabic', font_path))

    def generate_invoice(self, invoice_number):
        """توليد فاتورة بصيغة PDF"""
        try:
            # الحصول على بيانات الفاتورة
            self.database.ensure_connection()
            self.database.cursor.execute("""
                SELECT i.invoice_number,
                       c.brand || ' ' || c.model AS car_name,
                       c.chassis, c.engine,
                       cl.name AS client_name,
                       cl.phone AS client_phone,
                       cl.address AS client_address,
                       i.invoice_date,
                       i.total_amount,
                       i.payment_method,
                       i.payment_status,
                       u.username AS created_by
                FROM invoices i
                JOIN cars c ON i.car_id = c.id
                JOIN clients cl ON i.client_id = cl.id
                JOIN users u ON i.created_by = u.id
                WHERE i.invoice_number = ?
            """, (invoice_number,))
            
            invoice_data = self.database.cursor.fetchone()
            if not invoice_data:
                return False, "لم يتم العثور على الفاتورة"

            # إنشاء مجلد للفواتير إذا لم يكن موجوداً
            invoices_dir = os.path.join(os.path.dirname(self.database.db_path), 'invoices')
            os.makedirs(invoices_dir, exist_ok=True)
            
            # إنشاء ملف PDF
            filename = f"invoice_{invoice_number}.pdf"
            filepath = os.path.join(invoices_dir, filename)
            
            # إنشاء الفاتورة
            c = canvas.Canvas(filepath, pagesize=A4)
            width, height = A4
            
            # إعداد الخط
            c.setFont('Arabic', 16)
            
            # ترويسة الفاتورة
            self._draw_header(c, width, height)
            
            # بيانات الفاتورة
            self._draw_invoice_details(c, width, height, invoice_data)
            
            # بيانات السيارة
            self._draw_car_details(c, width, height, invoice_data)
            
            # بيانات العميل
            self._draw_client_details(c, width, height, invoice_data)
            
            # المبلغ والتوقيع
            self._draw_amount_and_signature(c, width, height, invoice_data)
            
            c.save()
            
            # تحديث مسار الملف في قاعدة البيانات
            self.database.cursor.execute("""
                UPDATE invoices
                SET file_path = ?
                WHERE invoice_number = ?
            """, (filename, invoice_number))
            
            self.database.conn.commit()
            
            return True, filepath
            
        except Exception as e:
            print(f"Error generating invoice: {str(e)}")
            return False, str(e)

    def _draw_header(self, canvas, width, height):
        """رسم ترويسة الفاتورة"""
        # شعار المعرض
        canvas.setFont('Arabic', 24)
        self._draw_arabic_text(canvas, "معرض أبو ريا موتورز", width/2, height-2*cm, align='center')
        
        canvas.setFont('Arabic', 18)
        self._draw_arabic_text(canvas, "لتجارة السيارات", width/2, height-3*cm, align='center')
        
        # معلومات الاتصال
        canvas.setFont('Arabic', 12)
        self._draw_arabic_text(canvas, "العنوان: القاهرة - مصر", width/2, height-4*cm, align='center')
        self._draw_arabic_text(canvas, "هاتف: 01234567890", width/2, height-4.7*cm, align='center')
        
        # عنوان الفاتورة
        canvas.setFont('Arabic', 20)
        self._draw_arabic_text(canvas, "فاتورة بيع سيارة", width/2, height-6*cm, align='center')
        
        # خط فاصل
        canvas.line(50, height-6.5*cm, width-50, height-6.5*cm)

    def _draw_invoice_details(self, canvas, width, height, data):
        """رسم تفاصيل الفاتورة"""
        canvas.setFont('Arabic', 14)
        
        # رقم الفاتورة والتاريخ
        self._draw_arabic_text(canvas, f"رقم الفاتورة: {data[0]}", 2*cm, height-8*cm)
        self._draw_arabic_text(canvas, f"التاريخ: {data[7]}", width-4*cm, height-8*cm)

    def _draw_car_details(self, canvas, width, height, data):
        """رسم تفاصيل السيارة"""
        canvas.setFont('Arabic', 14)
        
        # بيانات السيارة
        self._draw_arabic_text(canvas, "بيانات السيارة:", 2*cm, height-10*cm)
        canvas.setFont('Arabic', 12)
        self._draw_arabic_text(canvas, f"الماركة والموديل: {data[1]}", 3*cm, height-11*cm)
        self._draw_arabic_text(canvas, f"رقم الشاسيه: {data[2]}", 3*cm, height-12*cm)
        self._draw_arabic_text(canvas, f"رقم المحرك: {data[3]}", 3*cm, height-13*cm)

    def _draw_client_details(self, canvas, width, height, data):
        """رسم بيانات العميل"""
        canvas.setFont('Arabic', 14)
        
        # بيانات العميل
        self._draw_arabic_text(canvas, "بيانات المشتري:", 2*cm, height-15*cm)
        canvas.setFont('Arabic', 12)
        self._draw_arabic_text(canvas, f"الاسم: {data[4]}", 3*cm, height-16*cm)
        self._draw_arabic_text(canvas, f"رقم الهاتف: {data[5]}", 3*cm, height-17*cm)
        self._draw_arabic_text(canvas, f"العنوان: {data[6]}", 3*cm, height-18*cm)

    def _draw_amount_and_signature(self, canvas, width, height, data):
        """رسم المبلغ والتوقيع"""
        canvas.setFont('Arabic', 14)
        
        # المبلغ وطريقة الدفع
        amount_text = f"{data[8]:,.2f} جنيه مصري"
        self._draw_arabic_text(canvas, f"المبلغ: {amount_text}", 2*cm, height-20*cm)
        self._draw_arabic_text(canvas, f"طريقة الدفع: {data[9]}", 2*cm, height-21*cm)
        
        # إقرار الاستلام
        canvas.setFont('Arabic', 12)
        receipt_text = f"أقر أنا معرض أبو ريا موتورز باستلام مبلغ وقدره {amount_text} من السيد/ {data[4]}"
        self._draw_arabic_text(canvas, receipt_text, width/2, height-23*cm, align='center')
        
        # التوقيعات
        canvas.setFont('Arabic', 12)
        self._draw_arabic_text(canvas, "توقيع البائع", 3*cm, height-26*cm)
        self._draw_arabic_text(canvas, "توقيع المشتري", width-5*cm, height-26*cm)
        
        # خطوط التوقيع
        canvas.line(2*cm, height-27*cm, 6*cm, height-27*cm)
        canvas.line(width-6*cm, height-27*cm, width-2*cm, height-27*cm)
        
        # معلومات إضافية
        canvas.setFont('Arabic', 10)
        self._draw_arabic_text(canvas, f"تم إنشاء الفاتورة بواسطة: {data[11]}", 2*cm, height-29*cm)
        self._draw_arabic_text(canvas, f"تاريخ الطباعة: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", width-6*cm, height-29*cm)

    def _draw_arabic_text(self, canvas, text, x, y, align='right'):
        """رسم نص عربي مع معالجة اتجاه الكتابة"""
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        
        if align == 'center':
            canvas.drawCentredString(x, y, bidi_text)
        elif align == 'right':
            canvas.drawRightString(x, y, bidi_text)
        else:
            canvas.drawString(x, y, bidi_text)
