import os
import shutil
import sqlite3
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .utils import UIHelper
from .audit_log import audit_logger
from datetime import datetime

class BackupManagerDialog(QDialog):
    def __init__(self, database, current_user_id, current_username):
        super().__init__()
        self.database = database
        self.current_user_id = current_user_id
        self.current_username = current_username
        # تحديد مجلد النسخ الاحتياطية في نفس مستوى مجلد التطبيق
        self.backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        os.makedirs(self.backup_dir, exist_ok=True)
        self.init_ui()

    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        self.setWindowTitle("إدارة النسخ الاحتياطي")
        self.setGeometry(100, 100, 1000, 600)
        
        layout = QVBoxLayout()
        
        # عنوان الصفحة
        title_label = QLabel("إدارة النسخ الاحتياطي")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # جدول النسخ الاحتياطية
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "تاريخ النسخة", 
            "حجم السجلات", 
            "حجم قاعدة البيانات",
            "عدد السجلات",
            "حالة النسخة"
        ])
        
        # تنسيق رأس الجدول
        header = self.table.horizontalHeader()
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #533483;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # تفعيل تحديد الصف كاملاً
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # تنسيق التحديد
        self.table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: rgba(83, 52, 131, 0.2);
                color: #000000;
            }
        """)
        
        layout.addWidget(self.table)

        # منطقة عرض التفاصيل
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                font-family: monospace;
                max-height: 150px;
            }
        """)
        layout.addWidget(self.details_text)

        # أزرار التحكم
        button_layout = QHBoxLayout()
        
        create_button = QPushButton("إنشاء نسخة احتياطية")
        create_button.clicked.connect(self.create_backup)
        create_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        restore_button = QPushButton("استرجاع النسخة المحددة")
        restore_button.clicked.connect(self.restore_backup)
        restore_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: black;
                border: none;
                padding: 8px;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        
        delete_button = QPushButton("حذف النسخة المحددة")
        delete_button.clicked.connect(self.delete_backup)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        refresh_button = QPushButton("تحديث القائمة")
        refresh_button.clicked.connect(self.load_backups)
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        
        button_layout.addWidget(create_button)
        button_layout.addWidget(restore_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(refresh_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # تحميل النسخ الاحتياطية عند فتح النافذة
        self.load_backups()

    def load_backups(self):
        """تحميل قائمة النسخ الاحتياطية"""
        try:
            if not os.path.exists(self.backup_dir):
                return
            
            # جمع معلومات النسخ الاحتياطية
            backups = []
            for item in os.listdir(self.backup_dir):
                if item.endswith('_audit.log.backup'):
                    timestamp = item.split('_audit.log.backup')[0]
                    log_file = os.path.join(self.backup_dir, item)
                    db_file = os.path.join(self.backup_dir, f"{timestamp}_database.db.backup")
                    
                    # حساب الأحجام
                    log_size = os.path.getsize(log_file) / 1024  # KB
                    db_size = os.path.getsize(db_file) / 1024 if os.path.exists(db_file) else 0
                    
                    # حساب عدد السجلات
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_count = sum(1 for line in f if line.strip() and not line.startswith('#'))
                    
                    backup_date = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
                    backups.append({
                        'timestamp': timestamp,
                        'date': backup_date.strftime('%Y-%m-%d %H:%M:%S'),
                        'log_size': f"{log_size:.1f} KB",
                        'db_size': f"{db_size:.1f} KB",
                        'log_count': log_count,
                        'status': 'كاملة' if os.path.exists(db_file) else 'جزئية'
                    })
            
            # ترتيب النسخ حسب التاريخ (الأحدث أولاً)
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # عرض النسخ في الجدول
            self.table.setRowCount(len(backups))
            for i, backup in enumerate(backups):
                self.table.setItem(i, 0, QTableWidgetItem(backup['date']))
                self.table.setItem(i, 1, QTableWidgetItem(backup['log_size']))
                self.table.setItem(i, 2, QTableWidgetItem(backup['db_size']))
                self.table.setItem(i, 3, QTableWidgetItem(str(backup['log_count'])))
                self.table.setItem(i, 4, QTableWidgetItem(backup['status']))
            
            # تحديث منطقة التفاصيل
            self.details_text.clear()
            if backups:
                self.details_text.setPlainText(
                    f"عدد النسخ الاحتياطية: {len(backups)}\n"
                    f"آخر نسخة: {backups[0]['date']}\n"
                    f"مجلد النسخ الاحتياطية: {self.backup_dir}"
                )
            
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"فشل في تحميل النسخ الاحتياطية: {str(e)}")

    def create_backup(self):
        """إنشاء نسخة احتياطية جديدة"""
        try:
            if not UIHelper.confirm_action(
                self,
                "تأكيد",
                "هل أنت متأكد من إنشاء نسخة احتياطية جديدة؟"
            ):
                return
            
            result, message = audit_logger.clear_logs()  # سيقوم بإنشاء نسخة احتياطية
            
            if result:
                audit_logger.log_event(
                    user_id=self.current_user_id,
                    username=self.current_username,
                    event_type="إنشاء_نسخة_احتياطية",
                    description="تم إنشاء نسخة احتياطية جديدة"
                )
                
                UIHelper.show_success(self, "نجاح", message)
                self.load_backups()
            else:
                UIHelper.show_error(self, "خطأ", message)
                
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"فشل في إنشاء النسخة الاحتياطية: {str(e)}")

    def restore_backup(self):
        """استرجاع النسخة الاحتياطية المحددة"""
        try:
            selected_items = self.table.selectedItems()
            if not selected_items:
                UIHelper.show_warning(self, "تنبيه", "الرجاء اختيار نسخة احتياطية للاسترجاع")
                return
            
            backup_date = selected_items[0].text()
            
            if not UIHelper.confirm_action(
                self,
                "تأكيد",
                f"هل أنت متأكد من استرجاع النسخة الاحتياطية المؤرخة {backup_date}؟\n"
                "سيتم إنشاء نسخة احتياطية من الوضع الحالي قبل الاسترجاع.\n"
                "يجب إغلاق التطبيق وإعادة تشغيله بعد الاسترجاع."
            ):
                return
            
            # تحديد ملف النسخة الاحتياطية
            timestamp = datetime.strptime(backup_date, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f"{timestamp}_audit.log.backup")
            db_backup = os.path.join(self.backup_dir, f"{timestamp}_database.db.backup")
            
            if not os.path.exists(backup_file):
                UIHelper.show_error(self, "خطأ", "لم يتم العثور على ملف النسخة الاحتياطية")
                return

            # استرجاع قاعدة البيانات أولاً
            if os.path.exists(db_backup):
                try:
                    # إغلاق الاتصال بقاعدة البيانات الحالي
                    self.database.close()
                    
                    # نسخ ملف قاعدة البيانات
                    shutil.copy2(db_backup, self.database.db_path)
                    
                    # إعادة فتح الاتصال بقاعدة البيانات
                    self.database.conn = sqlite3.connect(self.database.db_path)
                    self.database.cursor = self.database.conn.cursor()
                    
                    # إعادة إنشاء الجداول للتأكد من تطابق الهيكل
                    self.database.create_tables()
                    
                    # تأكيد نجاح استرجاع قاعدة البيانات
                    self.database.cursor.execute("SELECT COUNT(*) FROM clients")
                    clients_count = self.database.cursor.fetchone()[0]
                    self.database.cursor.execute("SELECT COUNT(*) FROM cars")
                    cars_count = self.database.cursor.fetchone()[0]
                    
                except Exception as e:
                    UIHelper.show_error(
                        self, 
                        "خطأ", 
                        f"فشل في استرجاع قاعدة البيانات: {str(e)}"
                    )
                    return

            # ثم استرجاع ملف السجلات
            result, message = audit_logger.restore_backup(backup_file)
            
            if result:
                audit_logger.log_event(
                    user_id=self.current_user_id,
                    username=self.current_username,
                    event_type="استرجاع_نسخة_احتياطية",
                    description=f"تم استرجاع النسخة الاحتياطية المؤرخة {backup_date}"
                )
                
                success_message = (
                    "تم استرجاع النسخة الاحتياطية بنجاح:\n"
                    f"- عدد العملاء: {clients_count}\n"
                    f"- عدد السيارات: {cars_count}\n\n"
                    "يجب إغلاق التطبيق وإعادة تشغيله لتطبيق التغييرات."
                )
                
                UIHelper.show_success(self, "نجاح", success_message)
            else:
                UIHelper.show_error(self, "خطأ", message)
                
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"فشل في استرجاع النسخة الاحتياطية: {str(e)}")

    def delete_backup(self):
        """حذف النسخة الاحتياطية المحددة"""
        try:
            selected_items = self.table.selectedItems()
            if not selected_items:
                UIHelper.show_warning(self, "تنبيه", "الرجاء اختيار نسخة احتياطية للحذف")
                return
            
            backup_date = selected_items[0].text()
            
            if not UIHelper.confirm_action(
                self,
                "تأكيد",
                f"هل أنت متأكد من حذف النسخة الاحتياطية المؤرخة {backup_date}؟\n"
                "لا يمكن التراجع عن هذا الإجراء."
            ):
                return
            
            # تحديد ملفات النسخة الاحتياطية
            timestamp = datetime.strptime(backup_date, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d_%H%M%S')
            log_file = os.path.join(self.backup_dir, f"{timestamp}_audit.log.backup")
            db_file = os.path.join(self.backup_dir, f"{timestamp}_database.db.backup")
            
            # حذف الملفات
            if os.path.exists(log_file):
                os.remove(log_file)
            if os.path.exists(db_file):
                os.remove(db_file)
            
            audit_logger.log_event(
                user_id=self.current_user_id,
                username=self.current_username,
                event_type="حذف_نسخة_احتياطية",
                description=f"تم حذف النسخة الاحتياطية المؤرخة {backup_date}"
            )
            
            UIHelper.show_success(self, "نجاح", "تم حذف النسخة الاحتياطية بنجاح")
            self.load_backups()
            
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"فشل في حذف النسخة الاحتياطية: {str(e)}")
