import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from ..utils import UIHelper

class AccountingManager:
    def __init__(self, database):
        self.database = database
        self.categories = {
            "إيراد": [
                "مبيعات سيارات",
                "أقساط",
                "صيانة",
                "عمولات",
                "إيرادات أخرى"
            ],
            "مصروف": [
                "مشتريات سيارات",
                "رواتب",
                "إيجارات",
                "مرافق",
                "صيانة",
                "مصروفات تسويق",
                "مصروفات إدارية",
                "مصروفات أخرى"
            ]
        }

    def save_entry(self, entry_type, category, amount, date, description, user_id):
        """حفظ عملية مالية جديدة"""
        try:
            # التأكد من وجود اتصال نشط بقاعدة البيانات
            self.database.ensure_connection()
            
            self.database.cursor.execute("""
                INSERT INTO financial_entries (
                    entry_type, category, amount, date,
                    description, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                entry_type,
                category,
                amount,
                date,
                description,
                user_id
            ))
            
            self.database.conn.commit()
            return True, None
            
        except Exception as e:
            print(f"Error in save_entry: {str(e)}")
            return False, str(e)

    def get_entries(self, start_date=None, end_date=None):
        """جلب العمليات المالية"""
        try:
            # التأكد من وجود اتصال نشط بقاعدة البيانات
            self.database.ensure_connection()
            
            query = """
                SELECT id, entry_type, category, amount,
                       date, description
                FROM financial_entries
            """
            params = []
            
            if start_date and end_date:
                query += " WHERE date BETWEEN ? AND ?"
                params.extend([start_date, end_date])
                
            query += " ORDER BY date DESC, id DESC"
            
            self.database.cursor.execute(query, params)
            entries = self.database.cursor.fetchall()
            
            return entries
            
        except Exception as e:
            print(f"Error in get_entries: {str(e)}")
            return []

    def update_entry(self, entry_id, entry_type, category, amount, date, description):
        """تحديث عملية مالية"""
        try:
            # التأكد من وجود اتصال نشط بقاعدة البيانات
            self.database.ensure_connection()
            
            self.database.cursor.execute("""
                UPDATE financial_entries
                SET entry_type = ?,
                    category = ?,
                    amount = ?,
                    date = ?,
                    description = ?
                WHERE id = ?
            """, (
                entry_type,
                category,
                amount,
                date,
                description,
                entry_id
            ))
            
            self.database.conn.commit()
            return True, None
            
        except Exception as e:
            print(f"Error in update_entry: {str(e)}")
            return False, str(e)

    def delete_entry(self, entry_id):
        """حذف عملية مالية"""
        try:
            # التأكد من وجود اتصال نشط بقاعدة البيانات
            self.database.ensure_connection()
            
            self.database.cursor.execute(
                "DELETE FROM financial_entries WHERE id = ?",
                (entry_id,)
            )
            
            self.database.conn.commit()
            return True, None
            
        except Exception as e:
            print(f"Error in delete_entry: {str(e)}")
            return False, str(e)

    def get_summary(self, start_date=None, end_date=None):
        """الحصول على ملخص العمليات المالية"""
        try:
            # التأكد من وجود اتصال نشط بقاعدة البيانات
            self.database.ensure_connection()
            
            query = """
                SELECT entry_type,
                       SUM(amount) as total,
                       COUNT(*) as count
                FROM financial_entries
            """
            params = []
            
            if start_date and end_date:
                query += " WHERE date BETWEEN ? AND ?"
                params.extend([start_date, end_date])
                
            query += " GROUP BY entry_type"
            
            self.database.cursor.execute(query, params)
            results = self.database.cursor.fetchall()
            
            summary = {
                "إيراد": {"total": 0, "count": 0},
                "مصروف": {"total": 0, "count": 0}
            }
            
            for entry_type, total, count in results:
                summary[entry_type] = {
                    "total": total,
                    "count": count
                }
            
            return summary
            
        except Exception as e:
            print(f"Error in get_summary: {str(e)}")
            return {
                "إيراد": {"total": 0, "count": 0},
                "مصروف": {"total": 0, "count": 0}
            }

    def get_categories(self, entry_type):
        """الحصول على فئات نوع العملية"""
        return self.categories.get(entry_type, [])
