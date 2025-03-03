from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFileDialog, QDateEdit, QScrollArea
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont
from datetime import datetime
import os
import shutil
import subprocess
import sys
import pandas as pd
from .utils import Validator, UIHelper, Constants

class CarManagement(QWidget):
    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.database = database
        self.selected_car_id = None
        self.contract_filename = None
        self.user_id = None
        self.username = None
        self.init_ui()
        self.load_cars()

    def set_user_info(self, user_id, username):
        """تعيين معلومات المستخدم"""
        self.user_id = user_id
        self.username = username

    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        
        # إنشاء منطقة قابلة للتمرير للنموذج
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(400)  # تحديد ارتفاع أقصى
        
        form_widget = QWidget()
        self.add_car_layout = QGridLayout()
        self.add_car_layout.setVerticalSpacing(10)
        self.add_car_layout.setHorizontalSpacing(20)
        
        # الماركة والموديل
        self.brand_combo = QComboBox()
        self.brand_combo.addItems(sorted(Constants.CAR_BRANDS.keys()))
        self.brand_combo.currentTextChanged.connect(self.update_models)
        self.add_car_layout.addWidget(QLabel("الماركة:"), 0, 0)
        self.add_car_layout.addWidget(self.brand_combo, 0, 1)
        
        self.model_combo = QComboBox()
        self.add_car_layout.addWidget(QLabel("الموديل:"), 0, 2)
        self.add_car_layout.addWidget(self.model_combo, 0, 3)
        
        # تحديث الموديلات للماركة الأولى
        self.update_models(self.brand_combo.currentText())
        
        # سنة الصنع ورقم الشاسيه
        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("سنة الصنع")
        self.add_car_layout.addWidget(QLabel("سنة الصنع:"), 1, 0)
        self.add_car_layout.addWidget(self.year_input, 1, 1)
        
        self.chassis_input = QLineEdit()
        self.chassis_input.setPlaceholderText("رقم الشاسيه")
        self.add_car_layout.addWidget(QLabel("رقم الشاسيه:"), 1, 2)
        self.add_car_layout.addWidget(self.chassis_input, 1, 3)
        
        # رقم المحرك والحالة
        self.engine_input = QLineEdit()
        self.engine_input.setPlaceholderText("رقم المحرك")
        self.add_car_layout.addWidget(QLabel("رقم المحرك:"), 2, 0)
        self.add_car_layout.addWidget(self.engine_input, 2, 1)
        
        self.condition_combo = QComboBox()
        self.condition_combo.addItems(Constants.CAR_CONDITIONS)
        self.add_car_layout.addWidget(QLabel("الحالة:"), 2, 2)
        self.add_car_layout.addWidget(self.condition_combo, 2, 3)
        
        # نوع المعاملة والسعر
        self.transaction_combo = QComboBox()
        self.transaction_combo.addItems(Constants.TRANSACTION_TYPES)
        self.add_car_layout.addWidget(QLabel("نوع المعاملة:"), 3, 0)
        self.add_car_layout.addWidget(self.transaction_combo, 3, 1)
        
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("السعر بالجنيه المصري")
        self.add_car_layout.addWidget(QLabel("السعر:"), 3, 2)
        self.add_car_layout.addWidget(self.price_input, 3, 3)
        
        # التواريخ
        self.purchase_date = QDateEdit()
        self.purchase_date.setCalendarPopup(True)
        self.purchase_date.setDate(QDate.currentDate())
        self.add_car_layout.addWidget(QLabel("تاريخ الشراء/البيع:"), 4, 0)
        self.add_car_layout.addWidget(self.purchase_date, 4, 1)
        
        self.license_expiry = QDateEdit()
        self.license_expiry.setCalendarPopup(True)
        self.license_expiry.setDate(QDate.currentDate())
        self.add_car_layout.addWidget(QLabel("تاريخ انتهاء الرخصة:"), 4, 2)
        self.add_car_layout.addWidget(self.license_expiry, 4, 3)
        
        # معلومات العميل
        self.client_name = QLineEdit()
        self.client_name.setPlaceholderText("اسم العميل")
        self.add_car_layout.addWidget(QLabel("اسم العميل:"), 5, 0)
        self.add_car_layout.addWidget(self.client_name, 5, 1)
        
        self.client_phone = QLineEdit()
        self.client_phone.setPlaceholderText("01xxxxxxxxx")
        self.add_car_layout.addWidget(QLabel("رقم الهاتف:"), 5, 2)
        self.add_car_layout.addWidget(self.client_phone, 5, 3)
        
        self.client_address = QLineEdit()
        self.client_address.setPlaceholderText("عنوان العميل")
        self.add_car_layout.addWidget(QLabel("العنوان:"), 6, 0)
        self.add_car_layout.addWidget(self.client_address, 6, 1, 1, 3)
        
        # العقد
        self.contract_button = QPushButton("رفع العقد")
        self.contract_button.clicked.connect(self.upload_contract)
        self.add_car_layout.addWidget(QLabel("العقد:"), 7, 0)
        self.add_car_layout.addWidget(self.contract_button, 7, 1)
        
        self.contract_status = QLabel("")
        self.add_car_layout.addWidget(QLabel("حالة العقد:"), 7, 2)
        self.add_car_layout.addWidget(self.contract_status, 7, 3)
        
        # أزرار الإجراءات
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("حفظ")
        self.save_button.clicked.connect(self.save_car)
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
        
        self.export_button = QPushButton("تصدير إلى Excel")
        self.export_button.clicked.connect(self.export_to_excel)
        self.export_button.setStyleSheet("""
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
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        
        self.add_car_layout.addLayout(button_layout, 8, 0, 1, 4)
        
        form_widget.setLayout(self.add_car_layout)
        scroll_area.setWidget(form_widget)
        main_layout.addWidget(scroll_area)

        # جدول السيارات
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        headers = [
            "الرقم", "الماركة", "الموديل", "سنة الصنع", "رقم الشاسيه",
            "رقم المحرك", "الحالة", "نوع المعاملة", "السعر",
            "تاريخ الشراء/البيع", "تاريخ انتهاء الرخصة", "العقد"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        
        # تفعيل تحديد الصف كاملاً
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # تنسيق التحديد
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
        main_layout.addWidget(self.table)
        
        # أزرار الجدول
        table_buttons_layout = QHBoxLayout()
        
        edit_button = QPushButton("تعديل")
        edit_button.clicked.connect(self.edit_car)
        
        delete_button = QPushButton("حذف")
        delete_button.clicked.connect(self.delete_car)
        
        table_buttons_layout.addWidget(edit_button)
        table_buttons_layout.addWidget(delete_button)
        main_layout.addLayout(table_buttons_layout)
        
        self.setLayout(main_layout)

    def update_models(self, brand):
        """تحديث قائمة الموديلات بناءً على الماركة المحددة"""
        self.model_combo.clear()
        if brand in Constants.CAR_BRANDS:
            self.model_combo.addItems(Constants.CAR_BRANDS[brand])

    def validate_inputs(self):
        """التحقق من صحة المدخلات"""
        if not self.year_input.text().strip():
            UIHelper.show_error(self, "خطأ", "يرجى إدخال سنة الصنع")
            return False
            
        if not Validator.validate_year(self.year_input.text()):
            UIHelper.show_error(self, "خطأ", "سنة الصنع غير صحيحة")
            return False
            
        if not Validator.validate_chassis(self.chassis_input.text()):
            UIHelper.show_error(self, "خطأ", "رقم الشاسيه غير صحيح")
            return False
            
        if not Validator.validate_engine(self.engine_input.text()):
            UIHelper.show_error(self, "خطأ", "رقم المحرك غير صحيح")
            return False
            
        if not Validator.validate_price(self.price_input.text()):
            UIHelper.show_error(self, "خطأ", "السعر غير صحيح")
            return False
            
        if not Validator.validate_phone(self.client_phone.text()):
            UIHelper.show_error(self, "خطأ", "رقم هاتف العميل غير صحيح")
            return False
            
        return True

    def get_client_status(self, transaction_type):
        """تحديد حالة العميل بناءً على نوع المعاملة"""
        status_map = {
            "بيع": "مشتري",    # عندما نبيع السيارة، العميل يكون مشتري
            "شراء": "بائع",    # عندما نشتري السيارة، العميل يكون بائع
            "حجز": "حجز سيارة",
            "صيانة": "عرض سيارة"
        }
        return status_map.get(transaction_type, "غير محدد")

    def save_car(self):
        """حفظ بيانات السيارة"""
        if not self.validate_inputs():
            return
            
        transaction_type = self.transaction_combo.currentText()
        client_status = self.get_client_status(transaction_type)
            
        car_data = (
            self.brand_combo.currentText(),
            self.model_combo.currentText(),
            int(self.year_input.text()),
            self.chassis_input.text().strip(),
            self.engine_input.text().strip(),
            self.condition_combo.currentText(),
            transaction_type,
            float(self.price_input.text()),
            self.purchase_date.date().toString(Qt.DateFormat.ISODate),
            self.license_expiry.date().toString(Qt.DateFormat.ISODate),
            self.contract_filename,
            self.client_name.text().strip(),
            self.client_phone.text().strip(),
            self.client_address.text().strip(),
            client_status
        )
        
        try:
            if not self.user_id or not self.username:
                raise ValueError("معلومات المستخدم غير متوفرة")

            # حفظ بيانات العميل أولاً
            client_data = (
                self.client_name.text().strip(),
                self.client_phone.text().strip(),
                self.client_address.text().strip(),
                client_status
            )
            self.database.add_client(client_data, self.user_id, self.username)
            
            # حفظ بيانات السيارة
            if self.selected_car_id:  # تعديل سيارة موجودة
                self.database.cursor.execute("""
                    UPDATE cars 
                    SET brand = ?, model = ?, year = ?, chassis = ?, 
                        engine = ?, condition = ?, transaction_type = ?,
                        price = ?, purchase_date = ?, license_expiry = ?,
                        contract_filename = ?, client_name = ?, client_phone = ?,
                        client_address = ?, client_status = ?
                    WHERE id = ?
                """, (*car_data, self.selected_car_id))
                self.database.conn.commit()
                UIHelper.show_success(self, "نجاح", "تم تحديث بيانات السيارة بنجاح")
            else:  # إضافة سيارة جديدة
                if self.database.add_car(car_data, self.user_id, self.username):
                    UIHelper.show_success(self, "نجاح", "تمت إضافة السيارة بنجاح")
                else:
                    UIHelper.show_error(self, "خطأ", "فشل في إضافة السيارة")
            
            self.clear_fields()
            self.load_cars()
            
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"حدث خطأ: {str(e)}")

    def load_cars(self):
        """تحميل بيانات السيارات"""
        try:
            self.database.cursor.execute("""
                SELECT id, brand, model, year, chassis, engine,
                       condition, transaction_type, price,
                       purchase_date, license_expiry,
                       contract_filename, contract_upload_date
                FROM cars
            """)
            cars = self.database.cursor.fetchall()
            
            self.table.setRowCount(len(cars))
            for i, car in enumerate(cars):
                for j, value in enumerate(car):
                    if j == 11:  # عمود العقد
                        if value:  # إذا كان هناك عقد
                            contract_btn = QPushButton("عرض العقد")
                            contract_btn.clicked.connect(
                                lambda checked, x=value, car_id=car[0]: self.show_contract(x, car_id)
                            )
                            self.table.setCellWidget(i, j, contract_btn)
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
            UIHelper.show_error(self, "خطأ", f"فشل في تحميل بيانات السيارات: {str(e)}")

    def export_to_excel(self):
        """تصدير بيانات السيارات إلى ملف Excel"""
        try:
            # الحصول على البيانات من قاعدة البيانات
            self.database.cursor.execute("""
                SELECT id, brand, model, year, chassis, engine,
                       condition, transaction_type, price,
                       purchase_date, license_expiry,
                       client_name, client_phone, client_address
                FROM cars
            """)
            cars = self.database.cursor.fetchall()
            
            # إنشاء DataFrame
            columns = [
                "الرقم", "الماركة", "الموديل", "سنة الصنع", "رقم الشاسيه",
                "رقم المحرك", "الحالة", "نوع المعاملة", "السعر",
                "تاريخ الشراء/البيع", "تاريخ انتهاء الرخصة",
                "اسم العميل", "رقم الهاتف", "العنوان"
            ]
            df = pd.DataFrame(cars, columns=columns)
            
            # اختيار مسار الحفظ
            file_path, _ = QFileDialog.getSaveFileName(
                self, "حفظ ملف Excel", "", 
                "Excel Files (*.xlsx);;All Files (*)"
            )
            
            if file_path:
                if not file_path.lower().endswith('.xlsx'):
                    file_path += '.xlsx'
                
                # حفظ الملف
                df.to_excel(file_path, index=False, sheet_name="بيانات السيارات")
                UIHelper.show_success(
                    self, 
                    "نجاح", 
                    f"تم تصدير البيانات بنجاح إلى:\n{file_path}"
                )
                
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"فشل في تصدير البيانات: {str(e)}")

    def clear_fields(self):
        """مسح الحقول"""
        self.brand_combo.setCurrentIndex(0)
        self.update_models(self.brand_combo.currentText())
        self.year_input.clear()
        self.chassis_input.clear()
        self.engine_input.clear()
        self.condition_combo.setCurrentIndex(0)
        self.transaction_combo.setCurrentIndex(0)
        self.price_input.clear()
        self.purchase_date.setDate(QDate.currentDate())
        self.license_expiry.setDate(QDate.currentDate())
        self.client_name.clear()
        self.client_phone.clear()
        self.client_address.clear()
        self.selected_car_id = None
        self.contract_filename = None
        self.contract_button.setText("رفع العقد")
        self.contract_status.clear()
        self.save_button.setText("حفظ")

    def on_table_item_clicked(self, item):
        """معالجة النقر على عنصر في الجدول"""
        row = item.row()
        self.selected_car_id = self.table.item(row, 0).text()
        
        # تحميل بيانات السيارة
        self.database.cursor.execute("""
            SELECT * FROM cars WHERE id = ?
        """, (self.selected_car_id,))
        car = self.database.cursor.fetchone()
        
        if car:
            self.brand_combo.setCurrentText(car[1])  # الماركة
            self.model_combo.setCurrentText(car[2])  # الموديل
            self.year_input.setText(str(car[3]))     # سنة الصنع
            self.chassis_input.setText(car[4])       # رقم الشاسيه
            self.engine_input.setText(car[5])        # رقم المحرك
            self.condition_combo.setCurrentText(car[6])    # الحالة
            self.transaction_combo.setCurrentText(car[7])  # نوع المعاملة
            self.price_input.setText(str(car[8]))    # السعر
            
            # تعيين التواريخ
            purchase_date = QDate.fromString(car[9], Qt.DateFormat.ISODate)
            if purchase_date.isValid():
                self.purchase_date.setDate(purchase_date)
                
            license_date = QDate.fromString(car[10], Qt.DateFormat.ISODate)
            if license_date.isValid():
                self.license_expiry.setDate(license_date)
            
            # معلومات العقد
            self.contract_filename = car[11]  # اسم ملف العقد
            if self.contract_filename:
                self.contract_button.setText("تحديث العقد")
                self.contract_status.setText(f"تم الرفع: {car[12]}")  # تاريخ رفع العقد
                self.contract_status.setStyleSheet("color: green")
            else:
                self.contract_button.setText("رفع العقد")
                self.contract_status.clear()
            
            # معلومات العميل
            self.client_name.setText(car[13])    # اسم العميل
            self.client_phone.setText(car[14])   # رقم هاتف العميل
            self.client_address.setText(car[15]) # عنوان العميل
            
            self.save_button.setText("تحديث")

    def edit_car(self):
        """تعديل السيارة المحددة"""
        if not self.selected_car_id:
            UIHelper.show_warning(self, "تحذير", "يرجى اختيار سيارة للتعديل")
            return

    def delete_car(self):
        """حذف السيارة المحددة"""
        if not self.selected_car_id:
            UIHelper.show_warning(self, "تحذير", "يرجى اختيار سيارة للحذف")
            return
        
        if UIHelper.confirm_action(self, "تأكيد", "هل أنت متأكد من حذف هذه السيارة؟"):
            try:
                # الحصول على اسم ملف العقد قبل الحذف
                self.database.cursor.execute(
                    "SELECT contract_filename FROM cars WHERE id = ?",
                    (self.selected_car_id,)
                )
                result = self.database.cursor.fetchone()
                contract_filename = result[0] if result else None
                
                # حذف السيارة من قاعدة البيانات
                self.database.cursor.execute(
                    "DELETE FROM cars WHERE id = ?", 
                    (self.selected_car_id,)
                )
                
                # محاولة حذف ملف العقد
                if contract_filename:
                    contract_path = self.database.get_contract_path(contract_filename)
                    if contract_path and os.path.exists(contract_path):
                        os.remove(contract_path)
                
                self.database.conn.commit()
                self.load_cars()
                self.clear_fields()
                UIHelper.show_success(self, "نجاح", "تم حذف السيارة بنجاح")
                
            except Exception as e:
                UIHelper.show_error(self, "خطأ", f"فشل في حذف السيارة: {str(e)}")

    def upload_contract(self):
        """رفع ملف العقد"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف العقد", "", 
            "PDF Files (*.pdf);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            # التحقق من صحة الملف
            if not file_path.lower().endswith('.pdf'):
                raise ValueError("يجب أن يكون ملف العقد بصيغة PDF")
                
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # حد أقصى 10 ميجابايت
                raise ValueError("حجم الملف كبير جداً. الحد الأقصى هو 10 ميجابايت")
            
            # إنشاء اسم فريد للملف
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            random_suffix = os.urandom(4).hex()
            new_filename = f"contract_{timestamp}_{random_suffix}.pdf"
            
            # نسخ الملف إلى مجلد العقود
            contract_path = os.path.join(self.database.contracts_dir, new_filename)
            shutil.copy2(file_path, contract_path)
            
            # تحديث واجهة المستخدم
            self.contract_filename = new_filename
            self.contract_button.setText("تم رفع العقد")
            self.contract_status.setText(f"تم الرفع: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.contract_status.setStyleSheet("color: green")
            
            # عرض رسالة نجاح
            UIHelper.show_success(
                self, 
                "نجاح", 
                f"تم رفع العقد بنجاح\nاسم الملف: {new_filename}"
            )
            
        except Exception as e:
            self.contract_filename = None
            self.contract_status.setText("فشل رفع العقد")
            self.contract_status.setStyleSheet("color: red")
            UIHelper.show_error(self, "خطأ", f"فشل في رفع العقد: {str(e)}")

    def show_contract(self, contract_filename, car_id):
        """عرض العقد في نافذة منبثقة"""
        try:
            if not contract_filename:
                UIHelper.show_error(self, "خطأ", "لم يتم تحديد ملف العقد")
                return
                
            self.selected_car_id = car_id

            contract_path = self.database.get_contract_path(contract_filename)
            if not contract_path or not os.path.exists(contract_path):
                UIHelper.show_error(self, "خطأ", "لم يتم العثور على ملف العقد")
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("عقد السيارة")
            dialog.setGeometry(100, 100, 800, 600)
            
            layout = QVBoxLayout()
            
            # معلومات العقد
            info_label = QLabel(f"""
                اسم الملف: {contract_filename}
                تاريخ الرفع: {datetime.fromtimestamp(os.path.getctime(contract_path)).strftime('%Y-%m-%d %H:%M:%S')}
                حجم الملف: {os.path.getsize(contract_path) / 1024:.1f} KB
            """)
            layout.addWidget(info_label)
            
            # الأزرار
            buttons_layout = QHBoxLayout()
            
            view_button = QPushButton("عرض العقد")
            view_button.clicked.connect(lambda: self.open_contract(contract_path))
            buttons_layout.addWidget(view_button)
            
            download_button = QPushButton("تحميل العقد")
            download_button.clicked.connect(lambda: self.download_contract(contract_path))
            buttons_layout.addWidget(download_button)
            
            update_button = QPushButton("تحديث العقد")
            update_button.clicked.connect(lambda: self.update_contract(contract_filename))
            buttons_layout.addWidget(update_button)
            
            close_button = QPushButton("إغلاق")
            close_button.clicked.connect(dialog.close)
            buttons_layout.addWidget(close_button)
            
            layout.addLayout(buttons_layout)
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"حدث خطأ أثناء عرض العقد: {str(e)}")

    def open_contract(self, contract_path):
        """فتح ملف العقد"""
        try:
            if sys.platform == 'win32':
                os.startfile(contract_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', contract_path])
            else:
                subprocess.run(['xdg-open', contract_path])
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"فشل في فتح العقد: {str(e)}")

    def download_contract(self, contract_path):
        """تحميل ملف العقد"""
        try:
            if not os.path.exists(contract_path):
                raise FileNotFoundError("لم يتم العثور على ملف العقد")
                
            default_name = os.path.basename(contract_path)
            save_path, _ = QFileDialog.getSaveFileName(
                self, "حفظ العقد", default_name, 
                "PDF Files (*.pdf);;All Files (*)"
            )
            
            if save_path:
                if not save_path.lower().endswith('.pdf'):
                    save_path += '.pdf'
                    
                shutil.copy2(contract_path, save_path)
                UIHelper.show_success(
                    self, 
                    "نجاح", 
                    f"تم حفظ العقد بنجاح في:\n{save_path}"
                )
                
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"فشل في تحميل العقد: {str(e)}")

    def update_contract(self, old_filename):
        """تحديث ملف العقد"""
        try:
            if not self.selected_car_id:
                raise ValueError("يرجى اختيار سيارة أولاً")
                
            new_contract_path, _ = QFileDialog.getOpenFileName(
                self, "اختر ملف العقد الجديد", "", 
                "PDF Files (*.pdf);;All Files (*)"
            )
            
            if not new_contract_path:
                return
                
            if not new_contract_path.lower().endswith('.pdf'):
                raise ValueError("يجب أن يكون ملف العقد بصيغة PDF")
                
            # إنشاء اسم جديد للملف
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            random_suffix = os.urandom(4).hex()
            new_filename = f"contract_{self.selected_car_id}_{timestamp}_{random_suffix}.pdf"
            
            # نسخ العقد الجديد
            new_contract_full_path = os.path.join(self.database.contracts_dir, new_filename)
            shutil.copy2(new_contract_path, new_contract_full_path)
            
            # تحديث قاعدة البيانات
            if not self.database.update_car_contract(self.selected_car_id, new_filename, self.user_id, self.username):
                raise Exception("فشل في تحديث بيانات العقد في قاعدة البيانات")
            
            # محاولة حذف العقد القديم
            if old_filename:
                old_path = self.database.get_contract_path(old_filename)
                if old_path and os.path.exists(old_path):
                    os.remove(old_path)
            
            self.load_cars()  # تحديث الجدول
            UIHelper.show_success(
                self, 
                "نجاح", 
                f"تم تحديث العقد بنجاح\nاسم الملف الجديد: {new_filename}"
            )
            
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"فشل في تحديث العقد: {str(e)}")
