import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit,
    QComboBox, QDateEdit, QCheckBox,
    QFileDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from .utils import UIHelper
from .audit_log import audit_logger
from datetime import datetime, timedelta

class LogViewerDialog(QDialog):
    def __init__(self, database, current_user_id, current_username):
        super().__init__()
        self.database = database
        self.current_user_id = current_user_id
        self.current_username = current_username
        self.init_ui()

    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        self.setWindowTitle("عرض سجلات النظام")
        self.setGeometry(100, 100, 900, 600)
        
        layout = QVBoxLayout()
        
        # عنوان الصفحة
        title_label = QLabel("سجلات النظام")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # أدوات التصفية
        filter_layout = QHBoxLayout()
        
        # تصفية حسب نوع الحدث
        self.event_type_combo = QComboBox()
        self.event_type_combo.addItems([
            'الكل',
            'تسجيل_دخول',
            'إضافة_سيارة',
            'تعديل_سيارة',
            'حذف_سيارة',
            'إضافة_عميل',
            'تعديل_عميل',
            'حذف_عميل',
            'إضافة_معاملة',
            'تعديل_معاملة',
            'حذف_معاملة',
            'إضافة_مستخدم',
            'تعديل_مستخدم',
            'تفعيل_مستخدم',
            'تعطيل_مستخدم'
        ])
        self.event_type_combo.currentTextChanged.connect(self.load_logs)
        filter_layout.addWidget(QLabel("نوع الحدث:"))
        filter_layout.addWidget(self.event_type_combo)
        
        # تصفية حسب التاريخ
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_from.dateChanged.connect(self.load_logs)
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.load_logs)
        
        filter_layout.addWidget(QLabel("من:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("إلى:"))
        filter_layout.addWidget(self.date_to)
        
        # خيار عرض الأحداث الفاشلة فقط
        self.show_failed_only = QCheckBox("عرض الأحداث الفاشلة فقط")
        self.show_failed_only.stateChanged.connect(self.load_logs)
        filter_layout.addWidget(self.show_failed_only)
        
        layout.addLayout(filter_layout)

        # منطقة عرض السجلات
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                font-family: monospace;
            }
        """)
        layout.addWidget(self.log_display)

        # أزرار التحكم
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("تحديث")
        refresh_button.clicked.connect(self.load_logs)
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        export_button = QPushButton("تصدير السجلات")
        export_button.clicked.connect(self.export_logs)
        export_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        
        clear_button = QPushButton("مسح السجلات")
        clear_button.clicked.connect(self.clear_logs)
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(export_button)
        button_layout.addWidget(clear_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # تحميل السجلات عند فتح النافذة
        self.load_logs()

    def load_logs(self):
        """تحميل وعرض السجلات"""
        try:
            # تحديد معايير التصفية
            event_type = self.event_type_combo.currentText()
            date_from = self.date_from.date().toString(Qt.DateFormat.ISODate)
            date_to = self.date_to.date().toString(Qt.DateFormat.ISODate)
            show_failed = self.show_failed_only.isChecked()
            
            # الحصول على السجلات
            logs = audit_logger.get_logs()
            
            # تصفية السجلات
            filtered_logs = []
            for log in logs:
                # تحليل السجل
                try:
                    log_date = datetime.strptime(log.split(' - ')[0], '%Y-%m-%d %H:%M:%S')
                    if date_from <= log_date.strftime('%Y-%m-%d') <= date_to:
                        if event_type == 'الكل' or event_type in log:
                            if not show_failed or (show_failed and 'فشل' in log):
                                filtered_logs.append(log)
                except:
                    continue
            
            # عرض السجلات
            self.log_display.clear()
            if filtered_logs:
                self.log_display.setPlainText('\n'.join(filtered_logs))
            else:
                self.log_display.setPlainText("لا توجد سجلات تطابق معايير البحث")
            
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"فشل في تحميل السجلات: {str(e)}")

    def export_logs(self):
        """تصدير السجلات إلى ملف"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"logs_export_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_display.toPlainText())
            
            audit_logger.log_event(
                user_id=self.current_user_id,
                username=self.current_username,
                event_type="تصدير_سجلات",
                description=f"تم تصدير السجلات إلى الملف: {filename}"
            )
            
            UIHelper.show_success(
                self,
                "نجاح",
                f"تم تصدير السجلات بنجاح إلى الملف:\n{filename}"
            )
            
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"فشل في تصدير السجلات: {str(e)}")

    def clear_logs(self):
        """مسح جميع السجلات"""
        if not UIHelper.confirm_action(
            self,
            "تأكيد",
            "هل أنت متأكد من مسح جميع السجلات؟ سيتم إنشاء نسخة احتياطية قبل المسح."
        ):
            return
            
        try:
            result, message = audit_logger.clear_logs()
            
            if result:
                audit_logger.log_event(
                    user_id=self.current_user_id,
                    username=self.current_username,
                    event_type="مسح_سجلات",
                    description="تم مسح جميع السجلات مع حفظ نسخة احتياطية"
                )
                
                UIHelper.show_success(self, "نجاح", message)
                self.load_logs()
            else:
                UIHelper.show_error(self, "خطأ", message)
                
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"فشل في مسح السجلات: {str(e)}")
