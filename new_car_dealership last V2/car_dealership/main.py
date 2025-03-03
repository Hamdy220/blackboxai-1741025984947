from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QStackedWidget, QLabel, QFrame,
    QDialog
)
from PyQt6.QtCore import Qt, QSize
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
                background-color: #1a1a2e;
            }}
            
            QWidget#centralWidget {{
                background-color: rgba(26, 26, 46, 0.85);
                border-radius: 20px;
                margin: 15px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            QWidget {{
                color: #e1e1e6;
            }}
            
            QLabel {{
                color: #e1e1e6;
                font-weight: bold;
                background-color: transparent;
                font-size: 14px;
                padding: 8px;
                letter-spacing: 0.5px;
            }}
            
            QPushButton {{
                background-color: #16213e;
                color: #ffffff;
                border: 1px solid #0f3460;
                padding: 12px 20px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 13px;
                min-width: 120px;
            }}
            
            QPushButton:hover {{
                background-color: #0f3460;
                border-color: #533483;
            }}

            QPushButton:pressed {{
                background-color: #0a2647;
            }}
            
            QStackedWidget {{
                background-color: rgba(26, 26, 46, 0.95);
                border-radius: 15px;
                padding: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            QLineEdit, QTextEdit, QComboBox {{
                background-color: rgba(15, 52, 96, 0.95);
                border: 2px solid #533483;
                padding: 12px;
                border-radius: 10px;
                color: #ffffff;
                font-size: 13px;
                selection-background-color: #533483;
                selection-color: white;
            }}
            
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border: 2px solid #e94560;
                background-color: rgba(26, 26, 46, 0.95);
            }}
            
            QTableWidget {{
                background-color: rgba(26, 26, 46, 0.97);
                border-radius: 15px;
                gridline-color: #533483;
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 8px;
                selection-background-color: rgba(233, 69, 96, 0.3);
            }}
            
            QHeaderView::section {{
                background-color: #0f3460;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
                border-radius: 8px;
                margin: 2px;
            }}
            
            QComboBox {{
                background-color: rgba(15, 52, 96, 0.95);
                border-radius: 10px;
                padding: 8px;
                min-width: 150px;
                color: white;
            }}
            
            QComboBox::drop-down {{
                border: none;
            }}
            
            QComboBox::down-arrow {{
                image: url(none);
                border: none;
            }}
            
            QScrollBar:vertical {{
                background-color: rgba(26, 26, 46, 0.5);
                width: 14px;
                border-radius: 7px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: #533483;
                border-radius: 7px;
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: #e94560;
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        # إنشاء القطعة المركزية
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # القائمة الجانبية
        sidebar = QWidget()
        sidebar.setMaximumWidth(250)
        sidebar.setMinimumWidth(250)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: rgba(52, 58, 64, 0.95);
                border-radius: 15px;
                margin: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            QPushButton {
                background-color: rgba(73, 80, 87, 0.95);
                color: #e1e1e6;
                border: none;
                border-radius: 10px;
                padding: 12px;
                text-align: right;
                margin: 5px 10px;
            }
            
            QPushButton:hover {
                background-color: rgba(108, 117, 125, 0.95);
                border-left: 4px solid #00a8ff;
            }
            
            QPushButton:pressed {
                background-color: rgba(73, 80, 87, 0.95);
            }
            
            QPushButton[active="true"] {
                background-color: rgba(108, 117, 125, 0.95);
                border-left: 4px solid #00a8ff;
            }
        """)
        
        sidebar_layout = QVBoxLayout()
        sidebar.setLayout(sidebar_layout)

        # عنوان القائمة
        title_label = QLabel("القائمة الرئيسية")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            color: #00a8ff;
            padding: 20px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 10px;
        """)
        sidebar_layout.addWidget(title_label)

        # معلومات المستخدم
        user_info = QLabel(f"""
        👤 المستخدم: {self.username}
        🔑 الدور: {self.role}
        """)
        user_info.setStyleSheet("""
            padding: 15px;
            background-color: rgba(73, 80, 87, 0.95);
            border-radius: 10px;
            font-weight: bold;
            color: #e1e1e6;
            margin: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        """)
        sidebar_layout.addWidget(user_info)

        sidebar_layout.addSpacing(20)

        # الأزرار الرئيسية مع الأيقونات
        self.car_button = QPushButton("  إدارة السيارات")
        self.car_button.setMinimumHeight(50)
        self.car_button.clicked.connect(lambda: self.show_page(0))
        self.car_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView))
        self.car_button.setIconSize(QSize(24, 24))

        self.client_button = QPushButton("  إدارة العملاء")
        self.client_button.setMinimumHeight(50)
        self.client_button.clicked.connect(lambda: self.show_page(1))
        self.client_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogOkButton))
        self.client_button.setIconSize(QSize(24, 24))

        if self.role in ['مدير', 'موظف_مبيعات']:
            sidebar_layout.addWidget(self.car_button)
            sidebar_layout.addWidget(self.client_button)
            
        if self.role in ['مدير', 'محاسب']:
            self.finance_button = QPushButton("  النظام المالي")
            self.finance_button.setMinimumHeight(50)
            self.finance_button.clicked.connect(lambda: self.show_page(2))
            self.finance_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogApplyButton))
            self.finance_button.setIconSize(QSize(24, 24))
            sidebar_layout.addWidget(self.finance_button)
        
        sidebar_layout.addStretch()

        # أزرار التحكم والخروج
        self.control_button = QPushButton("  لوحة التحكم")
        self.control_button.setMinimumHeight(40)
        self.control_button.clicked.connect(lambda: self.show_page(3))
        self.control_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        self.control_button.setIconSize(QSize(24, 24))
        
        self.logout_button = QPushButton("  تسجيل خروج")
        self.logout_button.setMinimumHeight(40)
        self.logout_button.clicked.connect(self.logout)
        self.logout_button.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogCancelButton))
        self.logout_button.setIconSize(QSize(24, 24))
        self.logout_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                text-align: right;
                margin: 5px 10px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        sidebar_layout.addWidget(self.control_button)
        sidebar_layout.addWidget(self.logout_button)

        # خط فاصل
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("""
            QFrame {
                border: 1px solid rgba(233, 69, 96, 0.3);
                margin: 0px 10px;
            }
        """)

        # منطقة المحتوى
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
        
        self.content_area.addWidget(self.car_page)
        self.content_area.addWidget(self.client_page)
        self.content_area.addWidget(self.finance_page)
        self.content_area.addWidget(self.control_page)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(separator)
        main_layout.addWidget(self.content_area)

        if self.role in ['مدير', 'موظف_مبيعات']:
            self.show_page(0)
        elif self.role == 'محاسب':
            self.show_page(2)

    def show_page(self, index):
        """عرض الصفحة المحددة"""
        try:
            buttons = []
            if hasattr(self, 'car_button'):
                buttons.append(self.car_button)
            if hasattr(self, 'client_button'):
                buttons.append(self.client_button)
            if hasattr(self, 'finance_button'):
                buttons.append(self.finance_button)
            if hasattr(self, 'control_button'):
                buttons.append(self.control_button)

            button_styles = {
                'active': """
                    background-color: #e94560;
                    color: white;
                    border: 1px solid #533483;
                    padding: 12px;
                    border-radius: 10px;
                    font-size: 13px;
                """,
                'finance': """
                    background-color: #533483;
                    color: white;
                    border: 1px solid #e94560;
                    padding: 12px;
                    border-radius: 10px;
                    font-size: 13px;
                """,
                'control': """
                    background-color: #0f3460;
                    color: white;
                    border: 1px solid #533483;
                    padding: 12px;
                    border-radius: 10px;
                    font-size: 13px;
                """,
                'default': """
                    background-color: #16213e;
                    color: white;
                    border: 1px solid #0f3460;
                    padding: 12px;
                    border-radius: 10px;
                    font-size: 13px;
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
                        background-color: #533483;
                        border-color: #e94560;
                    }}
                """)
            
            self.content_area.setCurrentIndex(index)
            
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"حدث خطأ أثناء عرض الصفحة: {str(e)}")

    def logout(self):
        """تسجيل الخروج من التطبيق"""
        if UIHelper.confirm_action(self, "تأكيد", "هل أنت متأكد من تسجيل الخروج؟"):
            audit_logger.log_event(
                user_id=self.user_id,
                username=self.username,
                event_type="تسجيل_خروج",
                description="تم تسجيل الخروج من النظام"
            )
            
            self.hide()
            
            from .login import LoginWindow
            login_dialog = LoginWindow(self.database)
            if login_dialog.exec() == QDialog.DialogCode.Accepted:
                self.user_id = login_dialog.user_id
                self.username = login_dialog.username
                self.role = login_dialog.role
                self.setWindowTitle(f"نظام إدارة معرض السيارات - أبو ريا موتورز ({self.username})")
                self.show()
            else:
                self.close()
