from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QStackedWidget, QLabel, QFrame,
    QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QImage, QPalette, QBrush
from pathlib import Path

from .car_management import CarManagement
from .client_management import ClientManagement
from .utils import UIHelper
from .audit_log import audit_logger
from .financial import FinancePage
from .control_widget import ControlWidget

class MainWindow(QMainWindow):
    def __init__(self, database, user_id, username, role):
        super().__init__()
        self.database = database
        self.user_id = user_id
        self.username = username
        self.role = role
        self.init_ui()

    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        self.setWindowTitle(f"نظام إدارة معرض السيارات - أبو ريا موتورز ({self.username})")
        self.setGeometry(100, 100, 1200, 700)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # إعداد الخلفية باستخدام QSS
        image_path = str(Path(__file__).parent / "assets" / "images" / "main_bg.jpg")
        self.setStyleSheet(f"""
            QMainWindow {{
                background-image: url({image_path});
                background-position: center;
                background-repeat: no-repeat;
                background-size: cover;
                background-color: #f8f9fa; /* لون احتياطي في حالة عدم تحميل الصورة */
            }}
            
            /* تنسيق القطعة المركزية */
            QWidget#centralWidget {{
                background-color: rgba(255, 255, 255, 0.75);
                border-radius: 15px;
                margin: 10px;
            }}
            
            /* تنسيق العناصر العامة */
            QWidget {{
                color: #2c3e50;
            }}
            
            /* تنسيق العناوين */
            QLabel {{
                color: #2c3e50;
                font-weight: bold;
                background-color: transparent;
                font-size: 14px;
                padding: 5px;
                text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.8);
            }}
            
            /* تنسيق الأزرار */
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.9);
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                color: #2c3e50;
                font-size: 13px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
            }}
            
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 1);
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
            }}

            QPushButton:pressed {{
                background-color: rgba(240, 240, 240, 1);
                transform: translateY(1px);
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
            }}
            
            /* تنسيق القوائم والمحتوى */
            QStackedWidget {{
                background-color: rgba(255, 255, 255, 0.92);
                border-radius: 15px;
                padding: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            
            /* تنسيق حقول الإدخال */
            QLineEdit, QTextEdit, QComboBox {{
                background-color: rgba(255, 255, 255, 0.95);
                border: 2px solid rgba(44, 62, 80, 0.2);
                padding: 10px;
                border-radius: 8px;
                color: #2c3e50;
                font-size: 13px;
                selection-background-color: #007bff;
                selection-color: white;
            }}
            
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border: 2px solid rgba(41, 128, 185, 0.6);
                background-color: white;
                box-shadow: 0 0 5px rgba(41, 128, 185, 0.3);
            }}
            
            /* تنسيق الجداول */
            QTableWidget {{
                background-color: rgba(255, 255, 255, 0.97);
                border-radius: 10px;
                gridline-color: rgba(44, 62, 80, 0.1);
                border: none;
                padding: 5px;
                selection-background-color: rgba(41, 128, 185, 0.2);
            }}
            
            QHeaderView::section {{
                background-color: rgba(44, 62, 80, 0.9);
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
                border-radius: 5px;
                margin: 1px;
            }}
            
            /* تنسيق القوائم المنسدلة */
            QComboBox {{
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 5px;
                padding: 5px;
            }}
            
            QComboBox::drop-down {{
                border: none;
            }}
            
            QComboBox::down-arrow {{
                image: url(none);
                border: none;
            }}
            
            /* تنسيق شريط التمرير */
            QScrollBar:vertical {{
                background-color: rgba(255, 255, 255, 0.5);
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: rgba(44, 62, 80, 0.5);
                border-radius: 6px;
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        # إنشاء القطعة المركزية مع خلفية شفافة
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)


        # إنشاء القائمة الجانبية مع خلفية شبه شفافة
        sidebar = QWidget()
        sidebar.setMaximumWidth(200)
        sidebar.setMinimumWidth(200)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.92);
                border-radius: 15px;
                margin: 8px;
                box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
            }
        """)
        sidebar_layout = QVBoxLayout()
        sidebar.setLayout(sidebar_layout)

        # إضافة عنوان للقائمة
        title_label = QLabel("القائمة الرئيسية")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title_label)

        # معلومات المستخدم مع تنسيق محسن
        user_info = QLabel(f"""
        المستخدم: {self.username}
        الدور: {self.role}
        """)
        user_info.setStyleSheet("""
            QLabel {
                padding: 12px;
                background-color: rgba(248, 249, 250, 0.95);
                border-radius: 8px;
                font-weight: bold;
                color: #2c3e50;
                margin: 5px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }
        """)
        sidebar_layout.addWidget(user_info)

        # إضافة مساحة بين المعلومات والأزرار
        sidebar_layout.addSpacing(20)

        # إنشاء الأزرار الرئيسية
        self.car_button = QPushButton("إدارة السيارات")
        self.car_button.setMinimumHeight(50)
        self.car_button.clicked.connect(lambda: self.show_page(0))

        self.client_button = QPushButton("إدارة العملاء")
        self.client_button.setMinimumHeight(50)
        self.client_button.clicked.connect(lambda: self.show_page(1))

        # إضافة الأزرار حسب صلاحيات المستخدم
        if self.role in ['مدير', 'موظف_مبيعات']:
            sidebar_layout.addWidget(self.car_button)
            sidebar_layout.addWidget(self.client_button)
            
        if self.role in ['مدير', 'محاسب']:
            # زر النظام المالي
            self.finance_button = QPushButton("النظام المالي")
            self.finance_button.setMinimumHeight(50)
            self.finance_button.clicked.connect(lambda: self.show_page(2))
            self.finance_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 8px;
                    font-size: 13px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                QPushButton:hover {
                    background-color: #218838;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
                }
                QPushButton:pressed {
                    transform: translateY(1px);
                    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                }
            """)
            sidebar_layout.addWidget(self.finance_button)
        
        # إضافة مساحة متغيرة
        sidebar_layout.addStretch()

        # إضافة الأزرار في الأسفل
        self.control_button = QPushButton("لوحة التحكم")
        self.control_button.setMinimumHeight(40)
        self.control_button.clicked.connect(lambda: self.show_page(3))
        self.control_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            QPushButton:hover {
                background-color: #138496;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
            }
            QPushButton:pressed {
                transform: translateY(1px);
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
            }
        """)
        
        self.logout_button = QPushButton("تسجيل خروج")
        self.logout_button.setMinimumHeight(40)
        self.logout_button.clicked.connect(self.logout)
        self.logout_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            QPushButton:hover {
                background-color: #c82333;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
            }
            QPushButton:pressed {
                transform: translateY(1px);
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
            }
        """)

        sidebar_layout.addWidget(self.control_button)
        sidebar_layout.addWidget(self.logout_button)

        # إنشاء خط فاصل بين القائمة والمحتوى
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)

        # إنشاء منطقة المحتوى
        self.content_area = QStackedWidget()
        
        # إنشاء الصفحات
        self.car_page = CarManagement(self.database)
        self.car_page.set_user_info(self.user_id, self.username)
        
        self.client_page = ClientManagement(self.database)
        self.client_page.set_user_info(self.user_id, self.username)

        self.finance_page = FinancePage(self.database)
        self.finance_page.set_user_info(self.user_id, self.username)

        self.control_page = ControlWidget(
            self.database,
            self.user_id,
            self.username,
            self.role
        )
        
        # إضافة الصفحات إلى منطقة المحتوى
        self.content_area.addWidget(self.car_page)        # index 0
        self.content_area.addWidget(self.client_page)     # index 1
        self.content_area.addWidget(self.finance_page)    # index 2
        self.content_area.addWidget(self.control_page)    # index 3

        # إضافة العناصر إلى التخطيط الرئيسي
        main_layout.addWidget(sidebar)
        main_layout.addWidget(separator)
        main_layout.addWidget(self.content_area)

        # عرض الصفحة المناسبة حسب دور المستخدم
        if self.role in ['مدير', 'موظف_مبيعات']:
            self.show_page(0)  # صفحة السيارات
        elif self.role == 'محاسب':
            self.show_page(2)  # فتح النظام المالي مباشرة

    def show_page(self, index):
        """عرض الصفحة المحددة"""
        try:
            # تحديث حالة الأزرار
            buttons = []
            if hasattr(self, 'car_button'):
                buttons.append(self.car_button)
            if hasattr(self, 'client_button'):
                buttons.append(self.client_button)
            if hasattr(self, 'finance_button'):
                buttons.append(self.finance_button)
            if hasattr(self, 'control_button'):
                buttons.append(self.control_button)

            # تحديث أنماط الأزرار
            button_styles = {
                'active': """
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 8px;
                    font-size: 13px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                """,
                'finance': """
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 8px;
                    font-size: 13px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                """,
                'control': """
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 8px;
                    font-size: 13px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                """,
                'default': """
                    background-color: #f8f9fa;
                    color: #212529;
                    border: none;
                    padding: 12px;
                    border-radius: 8px;
                    font-size: 13px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                """
            }

            for i, button in enumerate(buttons):
                if i == index:
                    style = button_styles['active']
                elif button == self.finance_button:
                    style = button_styles['finance']
                elif button == self.control_button:
                    style = button_styles['control']
                else:
                    style = button_styles['default']
                
                button.setStyleSheet(f"""
                    QPushButton {{
                        {style}
                    }}
                    QPushButton:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
                    }}
                    QPushButton:pressed {{
                        transform: translateY(1px);
                        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                    }}
                """)
            
            # عرض الصفحة المحددة
            self.content_area.setCurrentIndex(index)
            
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"حدث خطأ أثناء عرض الصفحة: {str(e)}")

    def logout(self):
        """تسجيل الخروج من التطبيق"""
        if UIHelper.confirm_action(self, "تأكيد", "هل أنت متأكد من تسجيل الخروج؟"):
            # تسجيل حدث تسجيل الخروج
            audit_logger.log_event(
                user_id=self.user_id,
                username=self.username,
                event_type="تسجيل_خروج",
                description="تم تسجيل الخروج من النظام"
            )
            
            # إخفاء النافذة الرئيسية
            self.hide()
            
            # إنشاء وعرض نافذة تسجيل الدخول
            from .login import LoginWindow
            login_dialog = LoginWindow(self.database)
            if login_dialog.exec() == QDialog.DialogCode.Accepted:
                # تحديث معلومات المستخدم وإعادة عرض النافذة الرئيسية
                self.user_id = login_dialog.user_id
                self.username = login_dialog.username
                self.role = login_dialog.role
                self.setWindowTitle(f"نظام إدارة معرض السيارات - أبو ريا موتورز ({self.username})")
                self.show()
            else:
                # إغلاق التطبيق إذا تم إلغاء تسجيل الدخول
                self.close()
