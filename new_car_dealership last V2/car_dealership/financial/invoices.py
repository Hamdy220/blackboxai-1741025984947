import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QDate, QUrl
from PyQt6.QtGui import QColor, QDesktopServices
from datetime import datetime
from ..utils.ui_helper import UIHelper

class InvoicesManager:
    def __init__(self, database):
        self.database = database

    def create_invoice(self, car_id, client_id, amount, payment_method, user_id):
        """إنشاء فاتورة جديدة"""
        try:
            # التأكد من وجود اتصال نشط بقاعدة البيانات
            self.database.ensure_connection()
            
            # إنشاء رقم فاتورة جديد
            current_date = datetime.now()
            year = current_date.strftime("%Y")
            month = current_date.strftime("%m")
            
            self.database.cursor.execute("""
                SELECT MAX(CAST(SUBSTR(invoice_number, -4) AS INTEGER))
                FROM invoices
                WHERE invoice_number LIKE ?
            """, (f"INV-{year}{month}%",))
            
            result = self.database.cursor.fetchone()
            last_sequence = result[0] if result[0] else 0
            new_sequence = str(last_sequence + 1).zfill(4)
            invoice_number = f"INV-{year}{month}-{new_sequence}"
            
            # حفظ الفاتورة
            self.database.cursor.execute("""
                INSERT INTO invoices (
                    invoice_number, car_id, client_id,
                    invoice_date, total_amount,
                    payment_method, payment_status,
                    created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                invoice_number,
                car_id,
                client_id,
                QDate.currentDate().toString(Qt.DateFormat.ISODate),
                amount,
                payment_method,
                "مدفوع" if payment_method == "نقدي" else "تقسيط",
                user_id
            ))
            
            # إضافة العملية المالية إذا كان الدفع نقدي
            if payment_method == "نقدي":
                self.database.cursor.execute("""
                    INSERT INTO financial_entries (
                        entry_type, category, amount,
                        date, description, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "إيراد",
                    "مبيعات سيارات",
                    amount,
                    QDate.currentDate().toString(Qt.DateFormat.ISODate),
                    f"فاتورة رقم {invoice_number}",
                    user_id
                ))
            
            self.database.conn.commit()
            
            # إنشاء ملف PDF للفاتورة
            from .invoice_generator import InvoiceGenerator
            generator = InvoiceGenerator(self.database)
            success, result = generator.generate_invoice(invoice_number)
            
            if not success:
                print(f"Error generating invoice PDF: {result}")
            
            return True, invoice_number, None
            
        except Exception as e:
            print(f"Error in create_invoice: {str(e)}")
            return False, None, str(e)

    def get_invoices(self, start_date=None, end_date=None, payment_method=None):
        """جلب الفواتير"""
        try:
            # التأكد من وجود اتصال نشط بقاعدة البيانات
            self.database.ensure_connection()
            
            query = """
                SELECT i.invoice_number,
                       c.brand || ' ' || c.model AS car_name,
                       cl.name AS client_name,
                       i.invoice_date,
                       i.total_amount,
                       i.payment_method,
                       i.payment_status
                FROM invoices i
                JOIN cars c ON i.car_id = c.id
                JOIN clients cl ON i.client_id = cl.id
            """
            params = []
            
            conditions = []
            if start_date and end_date:
                conditions.append("i.invoice_date BETWEEN ? AND ?")
                params.extend([start_date, end_date])
                
            if payment_method:
                conditions.append("i.payment_method = ?")
                params.append(payment_method)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY i.invoice_date DESC"
            
            self.database.cursor.execute(query, params)
            return self.database.cursor.fetchall()
            
        except Exception as e:
            print(f"Error in get_invoices: {str(e)}")
            return []

    def get_invoice_details(self, invoice_number):
        """جلب تفاصيل فاتورة"""
        try:
            # التأكد من وجود اتصال نشط بقاعدة البيانات
            self.database.ensure_connection()
            
            self.database.cursor.execute("""
                SELECT i.invoice_number,
                       c.brand || ' ' || c.model AS car_name,
                       cl.name AS client_name,
                       cl.phone AS client_phone,
                       i.invoice_date,
                       i.total_amount,
                       i.payment_method,
                       i.payment_status,
                       i.created_at,
                       u.username AS created_by
                FROM invoices i
                JOIN cars c ON i.car_id = c.id
                JOIN clients cl ON i.client_id = cl.id
                JOIN users u ON i.created_by = u.id
                WHERE i.invoice_number = ?
            """, (invoice_number,))
            
            return self.database.cursor.fetchone()
            
        except Exception as e:
            print(f"Error in get_invoice_details: {str(e)}")
            return None

    def get_invoice_file(self, invoice_number):
        """الحصول على مسار ملف الفاتورة"""
        try:
            self.database.ensure_connection()
            
            self.database.cursor.execute("""
                SELECT file_path
                FROM invoices
                WHERE invoice_number = ?
            """, (invoice_number,))
            
            result = self.database.cursor.fetchone()
            if result and result[0]:
                file_path = os.path.join(
                    os.path.dirname(self.database.db_path),
                    'invoices',
                    result[0]
                )
                if os.path.exists(file_path):
                    return True, file_path
                    
            return False, "لم يتم العثور على ملف الفاتورة"
            
        except Exception as e:
            print(f"Error in get_invoice_file: {str(e)}")
            return False, str(e)

    def view_invoice(self, invoice_number):
        """عرض الفاتورة"""
        try:
            success, result = self.get_invoice_file(invoice_number)
            if success:
                # فتح الملف باستخدام التطبيق الافتراضي
                url = QUrl.fromLocalFile(result)
                QDesktopServices.openUrl(url)
                return True, None
            return False, result
        except Exception as e:
            print(f"Error viewing invoice: {str(e)}")
            return False, str(e)

    def download_invoice(self, invoice_number):
        """تحميل الفاتورة"""
        try:
            success, result = self.get_invoice_file(invoice_number)
            if not success:
                return False, result
                
            # اختيار مكان حفظ الملف
            filename = os.path.basename(result)
            save_path, _ = QFileDialog.getSaveFileName(
                None,
                "حفظ الفاتورة",
                filename,
                "PDF Files (*.pdf)"
            )
            
            if save_path:
                import shutil
                shutil.copy2(result, save_path)
                return True, save_path
                
            return False, "تم إلغاء التحميل"
            
        except Exception as e:
            print(f"Error downloading invoice: {str(e)}")
            return False, str(e)

    def regenerate_invoice(self, invoice_number):
        """إعادة إنشاء ملف الفاتورة"""
        try:
            from .invoice_generator import InvoiceGenerator
            generator = InvoiceGenerator(self.database)
            return generator.generate_invoice(invoice_number)
            
        except Exception as e:
            print(f"Error in regenerate_invoice: {str(e)}")
            return False, str(e)

    def get_sales_summary(self, start_date=None, end_date=None):
        """الحصول على ملخص المبيعات"""
        try:
            # التأكد من وجود اتصال نشط بقاعدة البيانات
            self.database.ensure_connection()
            
            query = """
                SELECT payment_method,
                       COUNT(*) as count,
                       SUM(total_amount) as total
                FROM invoices
            """
            params = []
            
            if start_date and end_date:
                query += " WHERE invoice_date BETWEEN ? AND ?"
                params.extend([start_date, end_date])
                
            query += " GROUP BY payment_method"
            
            self.database.cursor.execute(query, params)
            results = self.database.cursor.fetchall()
            
            summary = {
                "نقدي": {"count": 0, "total": 0},
                "تقسيط": {"count": 0, "total": 0}
            }
            
            for method, count, total in results:
                summary[method] = {
                    "count": count,
                    "total": total
                }
            
            return summary
            
        except Exception as e:
            print(f"Error in get_sales_summary: {str(e)}")
            return {
                "نقدي": {"count": 0, "total": 0},
                "تقسيط": {"count": 0, "total": 0}
            }
