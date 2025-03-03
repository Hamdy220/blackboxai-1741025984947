from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QMessageBox,
    QApplication, QWidget
)
from PyQt6.QtGui import QPixmap, QFont, QScreen, QPalette, QBrush, QImage
from PyQt6.QtCore import Qt, QCoreApplication, QSize
from pathlib import Path

from .utils import UIHelper
from .audit_log import audit_logger

class LoginWindow(QDialog):
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.user_id = None
        self.role = None
        self.username = None
        self.init_ui()
        self.center()
        
    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        self.setWindowTitle("تسجيل الدخول - أبو ريا موتورز")
        self.setFixedSize(400, 300)  # تعيين حجم ثابت للنافذة
        
        # تعيين صورة الخلفية باستخدام المسار الديناميكي
        image_path = str(Path(__file__).parent / "assets" / "images" / "login_bg.jpg")
        bg_image = QImage(image_path)
        
        if not bg_image.isNull():
            # تحجيم الصورة لتناسب النافذة مع الحفاظ على جودتها
            scaled_image = bg_image.scaled(
                self.width(),
                self.height(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # تعيين الخلفية
            palette = self.palette()
            palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled_image))
            self.setPalette(palette)
            self.setAutoFillBackground(True)
        else:
            # في حالة عدم وجود الصورة، تعيين لون خلفية افتراضي
            self.setStyleSheet("background-color: #2c3e50;")
            print("تحذير: لم يتم العثور على صورة الخلفية في المسار:", image_path)

        # تنسيق العناصر مع تحسين الشفافية والمظهر
        self.setStyleSheet("""
            QLabel {
                color: white;
                background: rgba(0, 0, 0, 0.6);
                padding: 8px;
                border-radius: 6px;
                font-weight: bold;
            }
            QLineEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(255, 255, 255, 0.2);
                padding: 10px;
                border-radius: 6px;
                color: #333;
                font-size: 14px;
            }
            
            QLineEdit:focus {
                border: 2px solid rgba(255, 255, 255, 0.5);
                background: rgba(255, 255, 255, 1);
            }
            QPushButton {
                background: rgba(41, 128, 185, 0.9);
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                min-width: 120px;
                font-weight: bold;
                font-size: 14px;
            }
            
            QPushButton:hover {
                background: rgba(41, 128, 185, 1);
                transform: scale(1.05);
            }
            
            QPushButton:pressed {
                background: rgba(41, 128, 185, 0.8);
            }
        """)
        
        self.setup_layouts()
        
    def center(self):
        """توسيط النافذة على الشاشة"""
        screen = QApplication.primaryScreen().geometry()
        qr = self.frameGeometry()
        cp = screen.center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def setup_layouts(self):
        """إعداد تخطيطات الواجهة"""
        main_layout = QVBoxLayout()
        
        # العنوان
        title_label = QLabel("أبو ريا موتورز", self)
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # نموذج تسجيل الدخول
        form_layout = QFormLayout()
        form_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("أدخل اسم المستخدم")
        self.username_input.setMinimumWidth(200)
        form_layout.addRow("اسم المستخدم:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("أدخل كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumWidth(200)
        form_layout.addRow("كلمة المرور:", self.password_input)
        
        main_layout.addLayout(form_layout)
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        login_button = QPushButton("تسجيل الدخول")
        login_button.clicked.connect(self.login)
        # تنسيق زر تسجيل الدخول
        login_button.setProperty('class', 'primary')
        
        # تنسيق زر إعادة التعيين
        reset_button = QPushButton("إعادة تعيين")
        reset_button.clicked.connect(self.reset_fields)
        reset_button.setProperty('class', 'secondary')
        
        buttons_layout.addWidget(login_button)
        buttons_layout.addWidget(reset_button)
        main_layout.addLayout(buttons_layout)
        
        self.setLayout(main_layout)
    
    def login(self):
        """التحقق من صحة بيانات تسجيل الدخول"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            UIHelper.show_error(self, "خطأ", "يرجى إدخال اسم المستخدم وكلمة المرور")
            return
        
        result = self.database.verify_login(username, password)
        if result:
            user_id, role, username = result
            self.user_id = user_id      # حفظ معرف المستخدم
            self.role = role            # حفظ دور المستخدم
            self.username = username     # حفظ اسم المستخدم
            
            # تسجيل نجاح تسجيل الدخول
            audit_logger.log_event(
                user_id=self.user_id,
                username=self.username,
                event_type="تسجيل_دخول",
                description=f"تم تسجيل الدخول بنجاح كـ {self.role}"
            )
            
            self.accept()
        else:
            # تسجيل فشل محاولة تسجيل الدخول
            audit_logger.log_event(
                user_id=0,
                username=username,
                event_type="تسجيل_دخول",
                description="محاولة تسجيل دخول فاشلة",
                status="فشل"
            )
            
            UIHelper.show_error(self, "خطأ", "اسم المستخدم أو كلمة المرور غير صحيحة")
            self.password_input.clear()
    
    def reset_fields(self):
        """إعادة تعيين حقول الإدخال"""
        self.username_input.clear()
        self.password_input.clear()
        self.username_input.setFocus()

    def get_user_info(self):
        """إرجاع معلومات المستخدم المسجل دخوله"""
        return {
            'user_id': self.user_id,
            'role': self.role,
            'username': self.username
        }
