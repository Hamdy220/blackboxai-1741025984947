from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtGui import QFont

from .user_management import UserManagementDialog
from .log_viewer import LogViewerDialog
from .backup_manager import BackupManagerDialog
from .utils import UIHelper
from .audit_log import audit_logger

class ControlWidget(QWidget):
    def __init__(self, database, user_id, username, role):
        super().__init__()
        self.database = database
        self.user_id = user_id
        self.username = username
        self.role = role
        self.init_ui()

    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        layout = QVBoxLayout()
        
        # عنوان اللوحة
        title_label = QLabel("لوحة التحكم")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # معلومات المستخدم
        user_info = QLabel(f"""
        المستخدم الحالي: {self.username}
        الدور: {self.role}
        """)
        user_info.setStyleSheet("padding: 10px; background-color: #f8f9fa; border-radius: 5px;")
        layout.addWidget(user_info)
        
        # أزرار التحكم
        if self.role == 'مدير':
            # إدارة المستخدمين (للمدير فقط)
            users_button = QPushButton("إدارة المستخدمين")
            users_button.clicked.connect(self.show_user_management)
            users_button.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
            layout.addWidget(users_button)
        
        if self.role in ['مدير', 'محاسب']:
            # عرض السجلات (للمدير والمحاسب)
            logs_button = QPushButton("عرض سجلات النظام")
            logs_button.clicked.connect(self.show_log_viewer)
            logs_button.setStyleSheet("""
                QPushButton {
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #138496;
                }
            """)
            layout.addWidget(logs_button)
        
        if self.role == 'مدير':
            # إدارة النسخ الاحتياطي (للمدير فقط)
            backup_button = QPushButton("إدارة النسخ الاحتياطي")
            backup_button.clicked.connect(self.show_backup_manager)
            backup_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            layout.addWidget(backup_button)
        
        layout.addStretch()
        self.setLayout(layout)

    def show_user_management(self):
        """عرض نافذة إدارة المستخدمين"""
        dialog = UserManagementDialog(self.database, self.user_id, self.username)
        dialog.exec()

    def show_log_viewer(self):
        """عرض نافذة سجلات النظام"""
        dialog = LogViewerDialog(self.database, self.user_id, self.username)
        dialog.exec()

    def show_backup_manager(self):
        """عرض نافذة إدارة النسخ الاحتياطي"""
        dialog = BackupManagerDialog(self.database, self.user_id, self.username)
        dialog.exec()
