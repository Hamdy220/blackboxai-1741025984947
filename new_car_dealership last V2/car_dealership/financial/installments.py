from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QSpinBox, QMessageBox, QDialog,
    QDialogButtonBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from ..utils.ui_helper import UIHelper

class InstallmentsManager:
    def __init__(self, database):
        self.database = database

    def save_installment(self, car_id, client_id, total_amount, down_payment,
                        installment_count, start_date, notes, user_id):
        """حفظ قسط جديد"""
        try:
            # التأكد من وجود اتصال نشط بقاعدة البيانات
            self.database.ensure_connection()
            remaining_amount = total_amount - down_payment
            next_payment_date = QDate.fromString(start_date, Qt.DateFormat.ISODate).addMonths(1)
            
            self.database.cursor.execute("""
                INSERT INTO installments (
                    car_id, client_id, total_amount,
                    paid_amount, remaining_amount,
                    installment_count, start_date,
                    next_payment_date, status,
                    notes, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                car_id,
                client_id,
                total_amount,
                down_payment,
                remaining_amount,
                installment_count,
                start_date,
                next_payment_date.toString(Qt.DateFormat.ISODate),
                "جاري",
                notes,
                user_id
            ))
            
            installment_id = self.database.cursor.lastrowid
            
            # إضافة الدفعة المقدمة كعملية مالية
            if down_payment > 0:
                self.database.cursor.execute("""
                    INSERT INTO financial_entries (
                        entry_type, category, amount,
                        date, description, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "إيراد",
                    "أقساط",
                    down_payment,
                    start_date,
                    f"دفعة مقدمة للقسط رقم {installment_id}",
                    user_id
                ))
            
            self.database.conn.commit()
            return True, installment_id, None
            
        except Exception as e:
            return False, None, str(e)

    def record_payment(self, installment_id, amount, payment_date,
                      payment_method, notes, user_id):
        """تسجيل دفعة جديدة"""
        try:
            # التأكد من وجود اتصال نشط بقاعدة البيانات
            self.database.ensure_connection()
            # التحقق من القسط
            self.database.cursor.execute("""
                SELECT remaining_amount, next_payment_date
                FROM installments
                WHERE id = ?
            """, (installment_id,))
            
            result = self.database.cursor.fetchone()
            if not result:
                return False, "لم يتم العثور على القسط"
                
            remaining, next_date = result
            
            if amount > remaining:
                return False, "المبلغ المدخل أكبر من المبلغ المتبقي"
            
            # تسجيل الدفعة
            self.database.cursor.execute("""
                INSERT INTO installment_payments (
                    installment_id, payment_date,
                    amount, payment_method, notes,
                    created_by
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                installment_id,
                payment_date,
                amount,
                payment_method,
                notes,
                user_id
            ))
            
            # تحديث القسط
            new_remaining = remaining - amount
            new_status = "منتهي" if new_remaining == 0 else "جاري"
            next_payment_date = QDate.fromString(next_date, Qt.DateFormat.ISODate).addMonths(1)
            
            self.database.cursor.execute("""
                UPDATE installments
                SET remaining_amount = ?,
                    paid_amount = paid_amount + ?,
                    next_payment_date = ?,
                    status = ?
                WHERE id = ?
            """, (
                new_remaining,
                amount,
                next_payment_date.toString(Qt.DateFormat.ISODate),
                new_status,
                installment_id
            ))
            
            # إضافة العملية المالية
            self.database.cursor.execute("""
                INSERT INTO financial_entries (
                    entry_type, category, amount,
                    date, description, created_by
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "إيراد",
                "أقساط",
                amount,
                payment_date,
                f"دفعة للقسط رقم {installment_id}",
                user_id
            ))
            
            self.database.conn.commit()
            return True, None
            
        except Exception as e:
            return False, str(e)

    def get_installments(self, status=None, start_date=None, end_date=None):
        """جلب الأقساط"""
        try:
            # التأكد من وجود اتصال نشط بقاعدة البيانات
            self.database.ensure_connection()
            query = """
                SELECT i.id, c.brand || ' ' || c.model as car_name,
                       cl.name as client_name, i.total_amount,
                       i.paid_amount, i.remaining_amount,
                       i.installment_count, i.next_payment_date,
                       i.status
                FROM installments i
                JOIN cars c ON i.car_id = c.id
                JOIN clients cl ON i.client_id = cl.id
            """
            params = []
            
            conditions = []
            if status:
                conditions.append("i.status = ?")
                params.append(status)
                
            if start_date and end_date:
                conditions.append("i.next_payment_date BETWEEN ? AND ?")
                params.extend([start_date, end_date])
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += """
                ORDER BY 
                    CASE i.status 
                        WHEN 'متأخر' THEN 1 
                        WHEN 'جاري' THEN 2 
                        WHEN 'منتهي' THEN 3 
                    END,
                    i.next_payment_date ASC
            """
            
            self.database.cursor.execute(query, params)
            return self.database.cursor.fetchall()
            
        except Exception:
            return []

    def update_status(self):
        """تحديث حالة الأقساط"""
        try:
            # التأكد من وجود اتصال نشط بقاعدة البيانات
            self.database.ensure_connection()
            current_date = QDate.currentDate().toString(Qt.DateFormat.ISODate)
            
            # تحديث الأقساط المتأخرة
            self.database.cursor.execute("""
                UPDATE installments
                SET status = 'متأخر'
                WHERE status = 'جاري'
                AND next_payment_date < ?
                AND remaining_amount > 0
            """, (current_date,))
            
            # تحديث الأقساط المنتهية
            self.database.cursor.execute("""
                UPDATE installments
                SET status = 'منتهي'
                WHERE status IN ('جاري', 'متأخر')
                AND remaining_amount = 0
            """)
            
            self.database.conn.commit()
            return True, None
            
        except Exception as e:
            return False, str(e)

    def get_late_installments(self):
        """جلب الأقساط المتأخرة"""
        try:
            # التأكد من وجود اتصال نشط بقاعدة البيانات
            self.database.ensure_connection()
            current_date = QDate.currentDate().toString(Qt.DateFormat.ISODate)
            
            self.database.cursor.execute("""
                SELECT i.id, c.brand || ' ' || c.model as car_name,
                       cl.name as client_name, cl.phone,
                       i.remaining_amount, i.next_payment_date,
                       JULIANDAY(?) - JULIANDAY(i.next_payment_date) as days_late
                FROM installments i
                JOIN cars c ON i.car_id = c.id
                JOIN clients cl ON i.client_id = cl.id
                WHERE i.status = 'متأخر'
                ORDER BY days_late DESC
            """, (current_date,))
            
            return self.database.cursor.fetchall()
            
        except Exception:
            return []

    def delete_installment(self, installment_id):
        """حذف قسط"""
        try:
            # التأكد من وجود اتصال نشط بقاعدة البيانات
            self.database.ensure_connection()
            # حذف الدفعات المرتبطة
            self.database.cursor.execute(
                "DELETE FROM installment_payments WHERE installment_id = ?",
                (installment_id,)
            )
            
            # حذف القسط
            self.database.cursor.execute(
                "DELETE FROM installments WHERE id = ?",
                (installment_id,)
            )
            
            self.database.conn.commit()
            return True, None
            
        except Exception as e:
            return False, str(e)
