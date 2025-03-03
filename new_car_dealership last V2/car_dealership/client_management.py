from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from .utils import Validator, UIHelper, Constants

class ClientManagement(QWidget):
    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.database = database
        self.selected_client_id = None
        self.user_id = None
        self.username = None
        self.init_ui()
        self.load_clients()

    def set_user_info(self, user_id, username):
        """تعيين معلومات المستخدم"""
        self.user_id = user_id
        self.username = username

    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        layout = QVBoxLayout()
        
        # قسم إضافة عميل
        form_group = QWidget()
        self.add_client_layout = QFormLayout()
        
        # اسم العميل
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم العميل")
        self.add_client_layout.addRow("الاسم:", self.name_input)
        
        # رقم الهاتف
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("01xxxxxxxxx (رقم مصري)")
        self.add_client_layout.addRow("رقم الهاتف:", self.phone_input)
        
        # العنوان
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("عنوان العميل")
        self.add_client_layout.addRow("العنوان:", self.address_input)
        
        # الحالة
        self.status_combo = QComboBox()
        self.status_combo.addItems(Constants.CLIENT_STATUSES)
        self.add_client_layout.addRow("الحالة:", self.status_combo)
        
        # أزرار الإجراءات
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("حفظ")
        self.save_button.clicked.connect(self.save_client)
        
        self.cancel_button = QPushButton("إلغاء")
        self.cancel_button.clicked.connect(self.clear_fields)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        self.add_client_layout.addRow(button_layout)
        
        form_group.setLayout(self.add_client_layout)
        layout.addWidget(form_group)

        # جدول العملاء
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["الرقم", "الاسم", "رقم الهاتف", "العنوان", "الحالة"])
        
        # تفعيل تحديد الصف كاملاً
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # تنسيق التحديد والجدول
        self.table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: rgba(83, 52, 131, 0.2);  /* #533483 with opacity */
                color: #000000;
            }
        """)
        
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
        self.table.itemClicked.connect(self.on_table_item_clicked)
        layout.addWidget(self.table)
        
        # أزرار الجدول
        table_buttons_layout = QHBoxLayout()
        
        edit_button = QPushButton("تعديل")
        edit_button.clicked.connect(self.edit_client)
        
        delete_button = QPushButton("حذف")
        delete_button.clicked.connect(self.delete_client)
        
        refresh_button = QPushButton("تحديث")
        refresh_button.clicked.connect(self.load_clients)
        
        table_buttons_layout.addWidget(edit_button)
        table_buttons_layout.addWidget(delete_button)
        table_buttons_layout.addWidget(refresh_button)
        layout.addLayout(table_buttons_layout)
        
        self.setLayout(layout)

    def validate_inputs(self):
        """التحقق من صحة المدخلات"""
        if not self.name_input.text().strip():
            UIHelper.show_error(self, "خطأ", "يرجى إدخال اسم العميل")
            return False
            
        if not Validator.validate_phone(self.phone_input.text()):
            UIHelper.show_error(self, "خطأ", "رقم الهاتف غير صحيح - يجب أن يكون رقم مصري يبدأ بـ 01")
            return False
            
        if not self.address_input.text().strip():
            UIHelper.show_error(self, "خطأ", "يرجى إدخال عنوان العميل")
            return False
            
        return True

    def save_client(self):
        """حفظ بيانات العميل"""
        if not self.validate_inputs():
            return
            
        client_data = (
            self.name_input.text().strip(),
            self.phone_input.text().strip(),
            self.address_input.text().strip(),
            self.status_combo.currentText()
        )
        
        try:
            if self.selected_client_id:  # تعديل عميل موجود
                self.database.cursor.execute("""
                    UPDATE clients 
                    SET name = ?, phone = ?, address = ?, status = ?
                    WHERE id = ?
                """, (*client_data, self.selected_client_id))
                self.database.conn.commit()
                UIHelper.show_success(self, "نجاح", "تم تحديث بيانات العميل بنجاح")
            else:  # إضافة عميل جديد
                if not self.user_id or not self.username:
                    raise ValueError("معلومات المستخدم غير متوفرة")

                if self.database.add_client(client_data, self.user_id, self.username):
                    UIHelper.show_success(self, "نجاح", "تمت إضافة العميل بنجاح")
                else:
                    UIHelper.show_error(self, "خطأ", "فشل في إضافة العميل")
            
            self.clear_fields()
            self.load_clients()
            
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"حدث خطأ: {str(e)}")

    def load_clients(self):
        """تحميل بيانات العملاء"""
        try:
            self.database.cursor.execute("SELECT * FROM clients")
            clients = self.database.cursor.fetchall()
            
            self.table.setRowCount(len(clients))
            for i, client in enumerate(clients):
                for j, value in enumerate(client):
                    self.table.setItem(i, j, QTableWidgetItem(str(value)))
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"فشل في تحميل بيانات العملاء: {str(e)}")

    def clear_fields(self):
        """مسح الحقول"""
        self.name_input.clear()
        self.phone_input.clear()
        self.address_input.clear()
        self.status_combo.setCurrentIndex(0)
        self.selected_client_id = None
        self.save_button.setText("حفظ")

    def on_table_item_clicked(self, item):
        """معالجة النقر على عنصر في الجدول"""
        row = item.row()
        self.selected_client_id = self.table.item(row, 0).text()
        self.name_input.setText(self.table.item(row, 1).text())
        self.phone_input.setText(self.table.item(row, 2).text())
        self.address_input.setText(self.table.item(row, 3).text())
        self.status_combo.setCurrentText(self.table.item(row, 4).text())
        self.save_button.setText("تحديث")

    def edit_client(self):
        """تعديل العميل المحدد"""
        if not self.selected_client_id:
            UIHelper.show_warning(self, "تحذير", "يرجى اختيار عميل للتعديل")
            return

    def delete_client(self):
        """حذف العميل المحدد"""
        if not self.selected_client_id:
            UIHelper.show_warning(self, "تحذير", "يرجى اختيار عميل للحذف")
            return
        
        if UIHelper.confirm_action(self, "تأكيد", "هل أنت متأكد من حذف هذا العميل؟"):
            try:
                self.database.cursor.execute(
                    "DELETE FROM clients WHERE id = ?",
                    (self.selected_client_id,)
                )
                self.database.conn.commit()
                self.load_clients()
                self.clear_fields()
                UIHelper.show_success(self, "نجاح", "تم حذف العميل بنجاح")
            except Exception as e:
                UIHelper.show_error(self, "خطأ", f"فشل في حذف العميل: {str(e)}")
