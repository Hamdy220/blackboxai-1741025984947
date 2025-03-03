import sqlite3
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from .utils import UIHelper
from .security import Security
from .audit_log import audit_logger

class UserManagementDialog(QDialog):
    def __init__(self, database, current_user_id, current_username):
        super().__init__()
        self.database = database
        self.current_user_id = current_user_id
        self.current_username = current_username
        self.selected_user_id = None
        self.init_ui()
        self.load_users()

    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        self.setWindowTitle("إدارة المستخدمين")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        # نموذج إضافة/تعديل المستخدم
        form_group = QWidget()
        form_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("اسم المستخدم")
        form_layout.addRow("اسم المستخدم:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("كلمة المرور:", self.password_input)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(['مدير', 'موظف_مبيعات', 'محاسب'])
        form_layout.addRow("الدور:", self.role_combo)
        
        # أزرار الإجراءات
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("حفظ")
        self.save_button.clicked.connect(self.save_user)
        self.save_button.setStyleSheet("""
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
        
        self.cancel_button = QPushButton("إلغاء")
        self.cancel_button.clicked.connect(self.clear_fields)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        form_layout.addRow(button_layout)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # جدول المستخدمين
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        headers = ["الرقم", "اسم المستخدم", "الدور", "آخر تسجيل دخول", "تاريخ الإنشاء", "الحالة"]
        self.table.setHorizontalHeaderLabels(headers)
        
        # تنسيق رأس الجدول
        header = self.table.horizontalHeader()
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #007bff;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.table.itemClicked.connect(self.on_table_item_clicked)
        layout.addWidget(self.table)
        
        # أزرار الجدول
        table_buttons_layout = QHBoxLayout()
        
        activate_button = QPushButton("تفعيل")
        activate_button.clicked.connect(lambda: self.toggle_user_status(1))
        activate_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        deactivate_button = QPushButton("تعطيل")
        deactivate_button.clicked.connect(lambda: self.toggle_user_status(0))
        deactivate_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        table_buttons_layout.addWidget(activate_button)
        table_buttons_layout.addWidget(deactivate_button)
        layout.addLayout(table_buttons_layout)
        
        self.setLayout(layout)

    def load_users(self):
        """تحميل بيانات المستخدمين"""
        try:
            self.database.cursor.execute("""
                SELECT id, username, role, last_login, created_at, active
                FROM users
                ORDER BY id
            """)
            users = self.database.cursor.fetchall()
            
            self.table.setRowCount(len(users))
            for i, user in enumerate(users):
                for j, value in enumerate(user):
                    if j == 5:  # عمود الحالة
                        status = "مفعل" if value == 1 else "معطل"
                        item = QTableWidgetItem(status)
                        item.setForeground(QColor("#28a745") if value == 1 else QColor("#dc3545"))
                    else:
                        item = QTableWidgetItem(str(value if value is not None else ""))
                    
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(i, j, item)
                
                # تلوين الصف بالتناوب
                if i % 2 == 0:
                    for j in range(self.table.columnCount()):
                        if self.table.item(i, j):
                            self.table.item(i, j).setBackground(QColor("#f8f9fa"))
            
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"فشل في تحميل بيانات المستخدمين: {str(e)}")

    def save_user(self):
        """حفظ بيانات المستخدم"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        role = self.role_combo.currentText()
        
        if not username:
            UIHelper.show_error(self, "خطأ", "يرجى إدخال اسم المستخدم")
            return
            
        if not self.selected_user_id and not password:
            UIHelper.show_error(self, "خطأ", "يرجى إدخال كلمة المرور")
            return
        
        try:
            if self.selected_user_id:  # تعديل مستخدم موجود
                if password:  # إذا تم إدخال كلمة مرور جديدة
                    hashed_password = Security.hash_password(password)
                    self.database.cursor.execute("""
                        UPDATE users 
                        SET username = ?, password = ?, role = ?
                        WHERE id = ?
                    """, (username, hashed_password, role, self.selected_user_id))
                else:  # تحديث بدون تغيير كلمة المرور
                    self.database.cursor.execute("""
                        UPDATE users 
                        SET username = ?, role = ?
                        WHERE id = ?
                    """, (username, role, self.selected_user_id))
                
                audit_logger.log_event(
                    user_id=self.current_user_id,
                    username=self.current_username,
                    event_type="تعديل_مستخدم",
                    description=f"تم تعديل بيانات المستخدم: {username}"
                )
                
                UIHelper.show_success(self, "نجاح", "تم تحديث بيانات المستخدم بنجاح")
            else:  # إضافة مستخدم جديد
                hashed_password = Security.hash_password(password)
                self.database.cursor.execute("""
                    INSERT INTO users (username, password, role, active)
                    VALUES (?, ?, ?, 1)
                """, (username, hashed_password, role))
                
                audit_logger.log_event(
                    user_id=self.current_user_id,
                    username=self.current_username,
                    event_type="إضافة_مستخدم",
                    description=f"تم إضافة مستخدم جديد: {username}"
                )
                
                UIHelper.show_success(self, "نجاح", "تم إضافة المستخدم بنجاح")
            
            self.database.conn.commit()
            self.clear_fields()
            self.load_users()
            
        except sqlite3.IntegrityError:
            UIHelper.show_error(self, "خطأ", "اسم المستخدم موجود بالفعل")
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"فشل في حفظ بيانات المستخدم: {str(e)}")

    def toggle_user_status(self, active):
        """تفعيل/تعطيل المستخدم"""
        if not self.selected_user_id:
            UIHelper.show_warning(self, "تحذير", "يرجى اختيار مستخدم أولاً")
            return
            
        if self.selected_user_id == self.current_user_id:
            UIHelper.show_error(self, "خطأ", "لا يمكنك تعطيل حسابك الحالي")
            return
        
        try:
            self.database.cursor.execute("""
                UPDATE users 
                SET active = ?
                WHERE id = ?
            """, (active, self.selected_user_id))
            
            status = "تفعيل" if active == 1 else "تعطيل"
            username = self.table.item(self.table.currentRow(), 1).text()
            
            audit_logger.log_event(
                user_id=self.current_user_id,
                username=self.current_username,
                event_type=f"{status}_مستخدم",
                description=f"تم {status} المستخدم: {username}"
            )
            
            self.database.conn.commit()
            self.load_users()
            UIHelper.show_success(self, "نجاح", f"تم {status} المستخدم بنجاح")
            
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"فشل في {status} المستخدم: {str(e)}")

    def on_table_item_clicked(self, item):
        """معالجة النقر على عنصر في الجدول"""
        row = item.row()
        self.selected_user_id = int(self.table.item(row, 0).text())
        self.username_input.setText(self.table.item(row, 1).text())
        self.role_combo.setCurrentText(self.table.item(row, 2).text())
        self.password_input.clear()
        self.save_button.setText("تحديث")

    def clear_fields(self):
        """مسح الحقول"""
        self.username_input.clear()
        self.password_input.clear()
        self.role_combo.setCurrentIndex(0)
        self.selected_user_id = None
        self.save_button.setText("حفظ")
