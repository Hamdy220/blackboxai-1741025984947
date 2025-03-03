from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QMessageBox, QFileDialog, QTabWidget,
    QSpinBox
)
from PyQt6.QtCore import Qt, QDate, QUrl
from PyQt6.QtGui import QColor, QDesktopServices, QFont
from datetime import datetime
from .accounting import AccountingManager
from .installments import InstallmentsManager
from .invoices import InvoicesManager
from .reports import ReportsManager
from ..utils.ui_helper import UIHelper

class FinancePage(QWidget):
    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.database = database
        
        # إنشاء مديري الوحدات
        self.accounting_manager = AccountingManager(database)
        self.installments_manager = InstallmentsManager(database)
        self.invoices_manager = InvoicesManager(database)
        self.reports_manager = ReportsManager(database)
        
        # تهيئة المتغيرات
        self.car_select = None
        self.client_select = None
        self.invoice_car = None
        self.invoice_client = None
        
        # تنسيق رؤوس الجداول
        self.header_style = """
            QHeaderView::section {
                background-color: #C11B17;
                color: white;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
        """
        
        self.init_ui()

    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        layout = QVBoxLayout()
        
        # عنوان الصفحة
        title = QLabel("النظام المالي")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # إنشاء مجموعة التبويبات
        self.tab_widget = QTabWidget()
        self.tab_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # إضافة التبويبات
        self.accounting_tab = self.create_accounting_tab()
        self.tab_widget.addTab(self.accounting_tab, "المحاسبة")
        
        self.installments_tab = self.create_installments_tab()
        self.tab_widget.addTab(self.installments_tab, "الأقساط")
        
        self.invoices_tab = self.create_invoices_tab()
        self.tab_widget.addTab(self.invoices_tab, "الفواتير")
        
        self.reports_tab = self.create_reports_tab()
        self.tab_widget.addTab(self.reports_tab, "التقارير")
        
        # ربط حدث تغيير التبويب بدالة التحديث
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def on_tab_changed(self, index):
        """تحديث البيانات عند تغيير التبويب"""
        try:
            if index == 0:  # تبويب المحاسبة
                self.load_accounting_entries()
            elif index == 1:  # تبويب الأقساط
                self.load_installments()
            elif index == 2:  # تبويب الفواتير
                self.load_invoices()
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"حدث خطأ أثناء تحديث البيانات: {str(e)}")

    def set_user_info(self, user_id, username):
        """تعيين معلومات المستخدم"""
        self.user_id = user_id
        self.username = username
        # تحديث البيانات عند فتح النظام المالي لأول مرة
        self.load_accounting_entries()
        self.load_installments()
        self.load_invoices()

    def create_accounting_tab(self):
        """إنشاء تبويب المحاسبة"""
        tab = QWidget()
        layout = QVBoxLayout()

        # نموذج إدخال البيانات
        form = QFormLayout()
        
        # نوع العملية
        self.operation_type = QComboBox()
        self.operation_type.addItems(["إيراد", "مصروف"])
        self.operation_type.currentTextChanged.connect(self.update_categories)
        form.addRow("نوع العملية:", self.operation_type)
        
        # فئة العملية
        self.category_combo = QComboBox()
        form.addRow("فئة العملية:", self.category_combo)
        
        # المبلغ
        self.amount = QLineEdit()
        form.addRow("المبلغ:", self.amount)
        
        # التاريخ
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setCalendarPopup(True)
        form.addRow("التاريخ:", self.date)
        
        # الوصف
        self.description = QLineEdit()
        form.addRow("الوصف:", self.description)
        
        # أزرار
        buttons = QHBoxLayout()
        save_btn = QPushButton("حفظ")
        save_btn.clicked.connect(self.save_accounting_entry)
        clear_btn = QPushButton("مسح")
        clear_btn.clicked.connect(self.clear_accounting_form)
        
        buttons.addWidget(save_btn)
        buttons.addWidget(clear_btn)
        
        layout.addLayout(form)
        layout.addLayout(buttons)
        
        # جدول العمليات المالية
        self.accounting_table = QTableWidget()
        self.accounting_table.setColumnCount(5)
        self.accounting_table.setHorizontalHeaderLabels([
            "نوع العملية", "المبلغ", "التاريخ", "الوصف", "الرصيد"
        ])
        
        # تنسيق الجدول
        self.accounting_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.accounting_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setup_table_header(self.accounting_table, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.accounting_table)
        
        # تحديث الفئات
        self.update_categories(self.operation_type.currentText())
        
        tab.setLayout(layout)
        return tab

    def create_invoices_tab(self):
        """إنشاء تبويب الفواتير"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # نموذج إنشاء فاتورة جديدة
        form = QFormLayout()
        
        # رقم الفاتورة
        self.invoice_number = QLineEdit()
        self.invoice_number.setEnabled(False)
        self.invoice_number.setPlaceholderText("سيتم إنشاؤه تلقائياً")
        form.addRow("رقم الفاتورة:", self.invoice_number)
        
        # السيارة
        self.invoice_car = QComboBox()
        form.addRow("السيارة:", self.invoice_car)
        
        # العميل
        self.invoice_client = QComboBox()
        form.addRow("العميل:", self.invoice_client)
        
        # المبلغ
        self.invoice_amount = QLineEdit()
        self.invoice_amount.setPlaceholderText("مبلغ الفاتورة")
        form.addRow("المبلغ:", self.invoice_amount)
        
        # طريقة الدفع
        self.payment_method = QComboBox()
        self.payment_method.addItems(["نقدي", "تقسيط"])
        form.addRow("طريقة الدفع:", self.payment_method)
        
        # أزرار
        buttons = QHBoxLayout()
        create_btn = QPushButton("إنشاء فاتورة")
        create_btn.clicked.connect(self.create_invoice)
        clear_btn = QPushButton("مسح")
        clear_btn.clicked.connect(self.clear_invoice_form)
        
        buttons.addWidget(create_btn)
        buttons.addWidget(clear_btn)
        
        layout.addLayout(form)
        layout.addLayout(buttons)
        
        # جدول الفواتير
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(9)  # Added 2 columns for actions
        self.invoices_table.setHorizontalHeaderLabels([
            "رقم الفاتورة", "السيارة", "العميل",
            "التاريخ", "المبلغ", "طريقة الدفع", "الحالة",
            "عرض", "تحميل"
        ])
        
        # تنسيق الجدول
        self.invoices_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.invoices_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # تنسيق رأس الجدول
        header = self.invoices_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setStyleSheet(self.header_style)
        
        layout.addWidget(self.invoices_table)
        
        # تحديث البيانات
        self.load_cars()
        self.load_clients()
        self.load_invoices()
        
        tab.setLayout(layout)
        return tab

    def create_installments_tab(self):
        """إنشاء تبويب الأقساط"""
        tab = QWidget()
        layout = QVBoxLayout()

        # إنشاء جدول الأقساط
        self.installments_table = QTableWidget()
        self.installments_table.setColumnCount(9)
        self.installments_table.setHorizontalHeaderLabels([
            "الرقم", "السيارة", "العميل", "إجمالي المبلغ",
            "المدفوع", "المتبقي", "عدد الأقساط",
            "تاريخ القسط القادم", "الحالة"
        ])
        
        # تنسيق الجدول
        self.installments_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.installments_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # تنسيق الأعمدة بحيث تمتد لتملأ المساحة المتاحة
        self.setup_table_header(
            self.installments_table,
            QHeaderView.ResizeMode.ResizeToContents,
            stretch_columns=[1, 2]  # تمديد أعمدة السيارة والعميل
        )
        
        # نموذج إضافة قسط جديد
        form = QFormLayout()
        
        # السيارة
        self.car_select = QComboBox()
        self.car_select.currentIndexChanged.connect(self.update_installment_amount)
        form.addRow("السيارة:", self.car_select)
        
        # العميل
        self.client_select = QComboBox()
        self.client_select.currentIndexChanged.connect(self.update_installment_amount)
        form.addRow("العميل:", self.client_select)
        
        # المبلغ الإجمالي والمقدم
        amount_layout = QHBoxLayout()
        
        self.total_amount = QLineEdit()
        self.total_amount.setPlaceholderText("إجمالي المبلغ")
        self.total_amount.textChanged.connect(self.calculate_installment)
        
        self.down_payment = QLineEdit()
        self.down_payment.setPlaceholderText("الدفعة المقدمة")
        self.down_payment.textChanged.connect(self.calculate_installment)
        
        amount_layout.addWidget(QLabel("إجمالي المبلغ:"))
        amount_layout.addWidget(self.total_amount)
        amount_layout.addWidget(QLabel("المقدم:"))
        amount_layout.addWidget(self.down_payment)
        form.addRow(amount_layout)
        
        # عدد الأقساط
        self.installments_count = QSpinBox()
        self.installments_count.setMinimum(1)
        self.installments_count.setMaximum(60)
        self.installments_count.valueChanged.connect(self.calculate_installment)
        form.addRow("عدد الأقساط:", self.installments_count)
        
        # قيمة القسط
        self.installment_amount = QLabel("قيمة القسط: 0.00 ج.م")
        self.installment_amount.setStyleSheet("font-weight: bold; color: #28a745;")
        form.addRow("", self.installment_amount)
        
        # تاريخ البداية
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        form.addRow("تاريخ البداية:", self.start_date)
        
        # ملاحظات
        self.notes = QLineEdit()
        self.notes.setPlaceholderText("ملاحظات إضافية")
        form.addRow("ملاحظات:", self.notes)
        
        # أزرار
        buttons = QHBoxLayout()
        save_btn = QPushButton("حفظ")
        save_btn.clicked.connect(self.save_installment)
        clear_btn = QPushButton("مسح")
        clear_btn.clicked.connect(self.clear_installment_form)
        
        buttons.addWidget(save_btn)
        buttons.addWidget(clear_btn)
        
        # أزرار إضافية للجدول
        table_buttons = QHBoxLayout()
        
        edit_btn = QPushButton("تعديل القسط المحدد")
        edit_btn.clicked.connect(self.edit_installment)
        
        delete_btn = QPushButton("حذف القسط المحدد")
        delete_btn.clicked.connect(self.delete_installment)
        
        pay_btn = QPushButton("تسجيل دفعة")
        pay_btn.clicked.connect(self.record_payment)
        
        table_buttons.addWidget(edit_btn)
        table_buttons.addWidget(delete_btn)
        table_buttons.addWidget(pay_btn)
        table_buttons.addStretch()
        
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addLayout(table_buttons)
        layout.addWidget(self.installments_table)
        
        # تحديث البيانات
        self.load_cars()
        self.load_clients()
        self.load_installments()
        
        tab.setLayout(layout)
        return tab

    def calculate_installment(self):
        """حساب قيمة القسط"""
        try:
            total = float(self.total_amount.text() or "0")
            down = float(self.down_payment.text() or "0")
            count = self.installments_count.value()
            
            if total <= 0 or down < 0 or down >= total or count <= 0:
                self.installment_amount.setText("قيمة القسط: 0.00 ج.م")
                return
            
            remaining = total - down
            monthly = remaining / count
            
            self.installment_amount.setText(f"قيمة القسط: {monthly:,.2f} ج.م")
            
        except ValueError:
            self.installment_amount.setText("قيمة القسط: 0.00 ج.م")

    def save_installment(self):
        """حفظ قسط جديد"""
        try:
            # التحقق من إدخال السيارة
            if self.car_select.currentIndex() == -1:
                UIHelper.show_warning(self, "تنبيه", "يرجى اختيار السيارة")
                return

            # التحقق من إدخال العميل
            if self.client_select.currentIndex() == -1:
                UIHelper.show_warning(self, "تنبيه", "يرجى اختيار العميل")
                return

            # التحقق من إدخال المبلغ الإجمالي
            total_amount_text = self.total_amount.text().strip()
            if not total_amount_text:
                UIHelper.show_warning(self, "تنبيه", "يرجى إدخال المبلغ الإجمالي")
                return
                
            try:
                total_amount = float(total_amount_text)
            if total_amount <= 0 or not isinstance(total_amount, (int, float)):
                    UIHelper.show_warning(self, "تنبيه", "يرجى إدخال مبلغ صحيح أكبر من الصفر")
                    return
            except ValueError:
                UIHelper.show_warning(self, "تنبيه", "يرجى إدخال مبلغ صحيح (أرقام فقط)")
                return

            # التحقق من إدخال الدفعة المقدمة
            down_payment_text = self.down_payment.text().strip()
            down_payment = 0.0  # القيمة الافتراضية
            
            if down_payment_text:  # إذا تم إدخال قيمة
                try:
                    down_payment = float(down_payment_text)
                    if down_payment < 0:
                        UIHelper.show_warning(self, "تنبيه", "يرجى إدخال دفعة مقدمة صحيحة (أكبر من أو تساوي الصفر)")
                        return
                    if down_payment >= total_amount:
                        UIHelper.show_warning(self, "تنبيه", "الدفعة المقدمة يجب أن تكون أقل من المبلغ الإجمالي")
                        return
                except ValueError:
                    UIHelper.show_warning(self, "تنبيه", "يرجى إدخال دفعة مقدمة صحيحة (أرقام فقط)")
                    return

            # التحقق من عدد الأقساط
            if self.installments_count.value() <= 0:
                UIHelper.show_warning(self, "تنبيه", "يرجى إدخال عدد أقساط صحيح أكبر من الصفر")
                return

            # التحقق من تاريخ البداية
            if not self.start_date.date().isValid():
                UIHelper.show_warning(self, "تنبيه", "يرجى إدخال تاريخ بداية صحيح")
                return

            # التحقق من صحة المبلغ باستخدام Validator
            from ..utils.validator import Validator
            if not Validator.validate_price(total_amount):
                UIHelper.show_warning(self, "تنبيه", "يرجى إدخال مبلغ صحيح")
                return

            # حفظ القسط
            success, installment_id, error = self.installments_manager.save_installment(
                self.car_select.currentData(),
                self.client_select.currentData(),
                total_amount,
                down_payment,
                self.installments_count.value(),
                self.start_date.date().toString(Qt.DateFormat.ISODate),
                self.notes.text(),
                self.user_id
            )
            
            if success:
                UIHelper.show_success(self, "نجاح", "تم حفظ القسط بنجاح")
                self.clear_installment_form()
                self.load_installments()
            else:
                UIHelper.show_error(self, "خطأ", f"حدث خطأ أثناء حفظ القسط: {error}")
                
        except Exception as e:
            UIHelper.show_error(self, "خطأ غير متوقع", f"حدث خطأ غير متوقع: {str(e)}")

    def clear_installment_form(self):
        """مسح نموذج الأقساط"""
        self.total_amount.clear()
        self.down_payment.clear()
        self.installments_count.setValue(1)
        self.start_date.setDate(QDate.currentDate())
        self.notes.clear()
        self.installment_amount.setText("قيمة القسط: 0.00 ج.م")

    def load_installments(self):
        """تحميل الأقساط"""
        installments = self.installments_manager.get_installments()
        self.installments_table.setRowCount(len(installments))
        
        for i, inst in enumerate(installments):
            inst_id, car, client, total, paid, remaining, count, next_date, status = inst
            
            self.installments_table.setItem(i, 0, QTableWidgetItem(str(inst_id)))
            self.installments_table.setItem(i, 1, QTableWidgetItem(car))
            self.installments_table.setItem(i, 2, QTableWidgetItem(client))
            self.installments_table.setItem(i, 3, QTableWidgetItem(f"{total:,.2f}"))
            self.installments_table.setItem(i, 4, QTableWidgetItem(f"{paid:,.2f}"))
            self.installments_table.setItem(i, 5, QTableWidgetItem(f"{remaining:,.2f}"))
            self.installments_table.setItem(i, 6, QTableWidgetItem(str(count)))
            self.installments_table.setItem(i, 7, QTableWidgetItem(next_date))
            self.installments_table.setItem(i, 8, QTableWidgetItem(status))
            
            color = {
                'متأخر': '#fff3cd',
                'جاري': '#d1e7dd',
                'منتهي': '#e2e3e5'
            }.get(status, '#ffffff')
            
            for j in range(9):
                self.installments_table.item(i, j).setBackground(QColor(color))

    def edit_installment(self):
        """تعديل القسط المحدد"""
        selected = self.installments_table.selectedItems()
        if not selected:
            UIHelper.show_warning(self, "تنبيه", "الرجاء تحديد قسط للتعديل")
            return
            
        # TODO: Implement edit functionality
        pass

    def delete_installment(self):
        """حذف القسط المحدد"""
        selected = self.installments_table.selectedItems()
        if not selected:
            UIHelper.show_warning(self, "تنبيه", "الرجاء تحديد قسط للحذف")
            return
            
        row = selected[0].row()
        installment_id = int(self.installments_table.item(row, 0).text())
        
        if UIHelper.confirm_action(self, "تأكيد", "هل أنت متأكد من حذف هذا القسط؟"):
            success, error = self.installments_manager.delete_installment(installment_id)
            
            if success:
                UIHelper.show_success(self, "نجاح", "تم حذف القسط بنجاح")
                self.load_installments()
            else:
                UIHelper.show_error(self, "خطأ", f"حدث خطأ أثناء حذف القسط: {error}")

    def record_payment(self):
        """تسجيل دفعة جديدة"""
        selected = self.installments_table.selectedItems()
        if not selected:
            UIHelper.show_warning(self, "تنبيه", "الرجاء تحديد قسط لتسجيل الدفعة")
            return
            
        row = selected[0].row()
        installment_id = int(self.installments_table.item(row, 0).text())
        
        # إنشاء نافذة تسجيل الدفعة
        dialog = QDialog(self)
        dialog.setWindowTitle("تسجيل دفعة جديدة")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        # المبلغ
        amount_input = QLineEdit()
        remaining = float(self.installments_table.item(row, 5).text().replace(",", ""))
        amount_input.setPlaceholderText(f"المبلغ المتبقي: {remaining:,.2f} ج.م")
        layout.addRow("المبلغ:", amount_input)
        
        # تاريخ الدفع
        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)
        layout.addRow("تاريخ الدفع:", date_input)
        
        # طريقة الدفع
        payment_method = QComboBox()
        payment_method.addItems(["نقدي", "شيك", "تحويل بنكي"])
        layout.addRow("طريقة الدفع:", payment_method)
        
        # ملاحظات
        notes_input = QLineEdit()
        notes_input.setPlaceholderText("ملاحظات إضافية")
        layout.addRow("ملاحظات:", notes_input)
        
        # أزرار
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                success, error = self.installments_manager.record_payment(
                    installment_id,
                    float(amount_input.text()),
                    date_input.date().toString(Qt.DateFormat.ISODate),
                    payment_method.currentText(),
                    notes_input.text(),
                    self.user_id
                )
                
                if success:
                    UIHelper.show_success(self, "نجاح", "تم تسجيل الدفعة بنجاح")
                    self.load_installments()
                else:
                    UIHelper.show_error(self, "خطأ", f"حدث خطأ أثناء تسجيل الدفعة: {error}")
                    
            except ValueError:
                UIHelper.show_warning(self, "تنبيه", "يرجى إدخال مبلغ صحيح")

    def create_reports_tab(self):
        """إنشاء تبويب التقارير"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # اختيار نوع التقرير
        self.report_type = QComboBox()
        self.report_type.addItems([
            "تقرير الإيرادات والمصروفات",
            "تقرير الأقساط",
            "تقرير المبيعات",
            "تقرير العملاء"
        ])
        layout.addWidget(QLabel("نوع التقرير:"))
        layout.addWidget(self.report_type)
        
        # فترة التقرير
        date_layout = QHBoxLayout()
        
        self.report_start_date = QDateEdit()
        self.report_start_date.setDate(QDate.currentDate())
        self.report_start_date.setCalendarPopup(True)
        
        self.report_end_date = QDateEdit()
        self.report_end_date.setDate(QDate.currentDate())
        self.report_end_date.setCalendarPopup(True)
        
        date_layout.addWidget(QLabel("من:"))
        date_layout.addWidget(self.report_start_date)
        date_layout.addWidget(QLabel("إلى:"))
        date_layout.addWidget(self.report_end_date)
        
        layout.addLayout(date_layout)
        
        # أزرار
        buttons = QHBoxLayout()
        generate_btn = QPushButton("إنشاء التقرير")
        generate_btn.clicked.connect(self.generate_report)
        export_btn = QPushButton("تصدير إلى Excel")
        export_btn.clicked.connect(self.export_report)
        
        buttons.addWidget(generate_btn)
        buttons.addWidget(export_btn)
        
        layout.addLayout(buttons)
        
        # جدول التقرير
        self.report_table = QTableWidget()
        self.report_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.report_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # تنسيق الأعمدة بحيث تمتد لتملأ المساحة المتاحة
        self.setup_table_header(
            self.report_table,
            QHeaderView.ResizeMode.Stretch  # جعل جميع الأعمدة تمتد بالتساوي
        )
        
        # ملخص التقرير
        self.report_summary = QLabel()
        self.report_summary.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        
        layout.addWidget(self.report_table)
        layout.addWidget(self.report_summary)
        
        tab.setLayout(layout)
        return tab

    def setup_table_header(self, table, stretch_mode=None, stretch_columns=None):
        """تنسيق رأس الجدول"""
        header = table.horizontalHeader()
        header.setStyleSheet(self.header_style)
        
        if stretch_mode:
            if stretch_columns:
                # تعيين النمط الافتراضي لجميع الأعمدة
                header.setSectionResizeMode(stretch_mode)
                # تعيين نمط خاص للأعمدة المحددة
                for col in stretch_columns:
                    header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
            else:
                # تعيين نفس النمط لجميع الأعمدة
                header.setSectionResizeMode(stretch_mode)
        
        return header

    def update_categories(self, operation_type):
        """تحديث فئات العمليات"""
        categories = self.accounting_manager.get_categories(operation_type)
        self.category_combo.clear()
        self.category_combo.addItems(categories)

    def save_accounting_entry(self):
        """حفظ عملية مالية جديدة"""
        try:
            if not self.amount.text().strip():
                UIHelper.show_warning(self, "تنبيه", "يرجى إدخال المبلغ")
                return
                
            if not self.description.text().strip():
                UIHelper.show_warning(self, "تنبيه", "يرجى إدخال وصف للعملية")
                return
            
            success, error = self.accounting_manager.save_entry(
                self.operation_type.currentText(),
                self.category_combo.currentText(),
                float(self.amount.text()),
                self.date.date().toString(Qt.DateFormat.ISODate),
                self.description.text(),
                self.user_id
            )
            
            if success:
                UIHelper.show_success(self, "نجاح", "تم حفظ العملية بنجاح")
                self.clear_accounting_form()
                self.load_accounting_entries()
            else:
                UIHelper.show_error(self, "خطأ", f"حدث خطأ أثناء حفظ العملية: {error}")
                
        except ValueError:
            UIHelper.show_warning(self, "تنبيه", "يرجى إدخال مبلغ صحيح")

    def clear_accounting_form(self):
        """مسح نموذج المحاسبة"""
        self.amount.clear()
        self.date.setDate(QDate.currentDate())
        self.description.clear()

    def load_accounting_entries(self):
        """تحميل العمليات المالية"""
        entries = self.accounting_manager.get_entries()
        self.accounting_table.setRowCount(len(entries))
        
        balance = 0
        for i, entry in enumerate(entries):
            entry_id, entry_type, category, amount, date, description = entry
            
            if entry_type == "إيراد":
                balance += amount
            else:
                balance -= amount
            
            self.accounting_table.setItem(i, 0, QTableWidgetItem(entry_type))
            self.accounting_table.setItem(i, 1, QTableWidgetItem(f"{amount:,.2f}"))
            self.accounting_table.setItem(i, 2, QTableWidgetItem(date))
            self.accounting_table.setItem(i, 3, QTableWidgetItem(description))
            self.accounting_table.setItem(i, 4, QTableWidgetItem(f"{balance:,.2f}"))
            
            color = "#d4edda" if entry_type == "إيراد" else "#f8d7da"
            for j in range(5):
                self.accounting_table.item(i, j).setBackground(QColor(color))

    def load_invoices(self):
        """تحميل الفواتير"""
        invoices = self.invoices_manager.get_invoices()
        self.invoices_table.setRowCount(len(invoices))
        
        for i, invoice in enumerate(invoices):
            invoice_number, car, client, date, amount, method, status = invoice
            
            self.invoices_table.setItem(i, 0, QTableWidgetItem(invoice_number))
            self.invoices_table.setItem(i, 1, QTableWidgetItem(car))
            self.invoices_table.setItem(i, 2, QTableWidgetItem(client))
            self.invoices_table.setItem(i, 3, QTableWidgetItem(date))
            self.invoices_table.setItem(i, 4, QTableWidgetItem(f"{amount:,.2f}"))
            self.invoices_table.setItem(i, 5, QTableWidgetItem(method))
            self.invoices_table.setItem(i, 6, QTableWidgetItem(status))
            
            # إضافة أزرار العرض والتحميل
            view_btn = QPushButton("عرض")
            view_btn.setStyleSheet("""
                QPushButton {
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #138496;
                }
            """)
            view_btn.clicked.connect(lambda checked, num=invoice_number: self.view_invoice(num))
            
            download_btn = QPushButton("تحميل")
            download_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            download_btn.clicked.connect(lambda checked, num=invoice_number: self.download_invoice(num))
            
            self.invoices_table.setCellWidget(i, 7, view_btn)
            self.invoices_table.setCellWidget(i, 8, download_btn)
            
            color = "#d4edda" if method == "نقدي" else "#fff3cd"
            for j in range(7):  # Don't color the button columns
                self.invoices_table.item(i, j).setBackground(QColor(color))

    def view_invoice(self, invoice_number):
        """عرض الفاتورة"""
        success, result = self.invoices_manager.view_invoice(invoice_number)
        if not success:
            UIHelper.show_error(self, "خطأ", result)

    def download_invoice(self, invoice_number):
        """تحميل الفاتورة"""
        success, result = self.invoices_manager.download_invoice(invoice_number)
        if success:
            UIHelper.show_success(
                self,
                "نجاح",
                f"تم حفظ الفاتورة في:\n{result}"
            )
        else:
            UIHelper.show_error(self, "خطأ", result)

    def create_invoice(self):
        """إنشاء فاتورة جديدة"""
        try:
            if not self.invoice_amount.text().strip():
                UIHelper.show_warning(self, "تنبيه", "يرجى إدخال مبلغ الفاتورة")
                return
                
            success, invoice_number, error = self.invoices_manager.create_invoice(
                self.invoice_car.currentData(),
                self.invoice_client.currentData(),
                float(self.invoice_amount.text()),
                self.payment_method.currentText(),
                self.user_id
            )
            
            if success:
                UIHelper.show_success(
                    self,
                    "نجاح",
                    f"تم إنشاء الفاتورة رقم {invoice_number} بنجاح"
                )
                self.clear_invoice_form()
                self.load_invoices()
            else:
                UIHelper.show_error(self, "خطأ", f"حدث خطأ أثناء إنشاء الفاتورة: {error}")
                
        except ValueError:
            UIHelper.show_warning(self, "تنبيه", "يرجى إدخال مبلغ صحيح")

    def clear_invoice_form(self):
        """مسح نموذج الفواتير"""
        self.invoice_number.clear()
        self.invoice_amount.clear()
        self.payment_method.setCurrentIndex(0)

    def generate_report(self):
        """توليد التقرير"""
        try:
            report_type = self.report_type.currentText()
            start_date = self.report_start_date.date().toString(Qt.DateFormat.ISODate)
            end_date = self.report_end_date.date().toString(Qt.DateFormat.ISODate)
            
            if report_type == "تقرير الإيرادات والمصروفات":
                success, results, summary, error = self.reports_manager.generate_financial_report(start_date, end_date)
                if success:
                    self.show_financial_report(results, summary)
                else:
                    UIHelper.show_error(self, "خطأ", f"فشل في توليد التقرير: {error}")
            elif report_type == "تقرير الأقساط":
                success, results, summary, error = self.reports_manager.generate_installments_report(start_date, end_date)
                if success:
                    self.show_installments_report(results, summary)
                else:
                    UIHelper.show_error(self, "خطأ", f"فشل في توليد التقرير: {error}")
            elif report_type == "تقرير المبيعات":
                success, results, summary, error = self.reports_manager.generate_sales_report(start_date, end_date)
                if success:
                    self.show_sales_report(results, summary)
                else:
                    UIHelper.show_error(self, "خطأ", f"فشل في توليد التقرير: {error}")
            else:  # تقرير العملاء
                success, results, summary, error = self.reports_manager.generate_clients_report(start_date, end_date)
                if success:
                    self.show_clients_report(results, summary)
                else:
                    UIHelper.show_error(self, "خطأ", f"فشل في توليد التقرير: {error}")
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"حدث خطأ أثناء توليد التقرير: {str(e)}")

    def show_financial_report(self, results, summary):
        """عرض تقرير الإيرادات والمصروفات"""
        self.report_table.clear()
        self.report_table.setRowCount(len(results))
        self.report_table.setColumnCount(4)
        self.report_table.setHorizontalHeaderLabels([
            "نوع العملية", "الفئة", "المبلغ", "عدد العمليات"
        ])
        
        for i, row in enumerate(results):
            entry_type, category, total, count = row
            
            self.report_table.setItem(i, 0, QTableWidgetItem(entry_type))
            self.report_table.setItem(i, 1, QTableWidgetItem(category))
            self.report_table.setItem(i, 2, QTableWidgetItem(f"{total:,.2f}"))
            self.report_table.setItem(i, 3, QTableWidgetItem(str(count)))
            
            color = "#d4edda" if entry_type == "إيراد" else "#f8d7da"
            for j in range(4):
                self.report_table.item(i, j).setBackground(QColor(color))
        
        self.report_summary.setText(f"""
            إجمالي الإيرادات: {summary['إيراد']['total']:,.2f} ج.م
            إجمالي المصروفات: {summary['مصروف']['total']:,.2f} ج.م
            صافي الربح/الخسارة: {summary['إيراد']['total'] - summary['مصروف']['total']:,.2f} ج.م
        """)

    def show_installments_report(self, results, summary):
        """عرض تقرير الأقساط"""
        self.report_table.clear()
        self.report_table.setRowCount(len(results))
        self.report_table.setColumnCount(9)
        self.report_table.setHorizontalHeaderLabels([
            "الرقم", "السيارة", "العميل", "إجمالي المبلغ",
            "المدفوع", "المتبقي", "عدد الأقساط",
            "تاريخ القسط القادم", "الحالة"
        ])
        
        for i, row in enumerate(results):
            for j, value in enumerate(row):
                if isinstance(value, float):
                    text = f"{value:,.2f}"
                else:
                    text = str(value)
                self.report_table.setItem(i, j, QTableWidgetItem(text))
            
            color = {
                'متأخر': '#fff3cd',
                'جاري': '#d1e7dd',
                'منتهي': '#e2e3e5'
            }.get(row[8], '#ffffff')
            
            for j in range(9):
                self.report_table.item(i, j).setBackground(QColor(color))
        
        self.report_summary.setText(f"""
            عدد الأقساط: {summary['total_count']}
            إجمالي المبالغ: {summary['total_amount']:,.2f} ج.م
            إجمالي المدفوع: {summary['total_paid']:,.2f} ج.م
            إجمالي المتبقي: {summary['total_remaining']:,.2f} ج.م
            
            جاري: {summary['status']['جاري']}
            متأخر: {summary['status']['متأخر']}
            منتهي: {summary['status']['منتهي']}
        """)

    def show_sales_report(self, results, summary):
        """عرض تقرير المبيعات"""
        self.report_table.clear()
        self.report_table.setRowCount(len(results))
        self.report_table.setColumnCount(7)
        self.report_table.setHorizontalHeaderLabels([
            "رقم الفاتورة", "السيارة", "العميل",
            "التاريخ", "المبلغ", "طريقة الدفع", "الحالة"
        ])
        
        for i, row in enumerate(results):
            for j, value in enumerate(row):
                if isinstance(value, float):
                    text = f"{value:,.2f}"
                else:
                    text = str(value)
                self.report_table.setItem(i, j, QTableWidgetItem(text))
            
            color = "#d4edda" if row[5] == "نقدي" else "#fff3cd"
            for j in range(7):
                self.report_table.item(i, j).setBackground(QColor(color))
        
        self.report_summary.setText(f"""
            عدد المبيعات: {summary['total_count']}
            إجمالي المبيعات: {summary['total_amount']:,.2f} ج.م
            
            المبيعات النقدية:
            العدد: {summary['payment_method']['نقدي']['count']}
            المبلغ: {summary['payment_method']['نقدي']['total']:,.2f} ج.م
            
            مبيعات التقسيط:
            العدد: {summary['payment_method']['تقسيط']['count']}
            المبلغ: {summary['payment_method']['تقسيط']['total']:,.2f} ج.م
        """)

    def show_clients_report(self, results, summary):
        """عرض تقرير العملاء"""
        self.report_table.clear()
        self.report_table.setRowCount(len(results))
        self.report_table.setColumnCount(6)
        self.report_table.setHorizontalHeaderLabels([
            "اسم العميل", "رقم الهاتف", "عدد الفواتير",
            "إجمالي المبيعات", "عدد الأقساط", "المبلغ المتبقي"
        ])
        
        for i, row in enumerate(results):
            for j, value in enumerate(row):
                if isinstance(value, float):
                    text = f"{value:,.2f}"
                elif value is None:
                    text = "0"
                else:
                    text = str(value)
                self.report_table.setItem(i, j, QTableWidgetItem(text))
        
        self.report_summary.setText(f"""
            عدد العملاء: {summary['total_clients']}
            إجمالي المبيعات: {summary['total_sales']:,.2f} ج.م
            إجمالي المبالغ المتبقية: {summary['total_remaining']:,.2f} ج.م
            عدد العملاء بأقساط: {summary['with_installments']}
        """)

    def save_installment(self):
        """حفظ القسط الجديد"""
        try:
            if not self.installment_amount.text().strip():
                UIHelper.show_warning(self, "تنبيه", "يرجى إدخال المبلغ")
                return
                
            if self.car_select.currentIndex() == -1:
                UIHelper.show_warning(self, "تنبيه", "يرجى اختيار السيارة")
                return
                
            if self.client_select.currentIndex() == -1:
                UIHelper.show_warning(self, "تنبيه", "يرجى اختيار العميل")
                return
            
            success, error = self.installments_manager.save_installment(
                self.car_select.currentData(),
                self.client_select.currentData(),
                float(self.installment_amount.text()),
                self.installment_count.value(),
                self.installment_start_date.date().toString(Qt.DateFormat.ISODate),
                self.user_id
            )
            
            if success:
                UIHelper.show_success(self, "نجاح", "تم حفظ القسط بنجاح")
                self.clear_installment_form()
                self.load_installments()
            else:
                UIHelper.show_error(self, "خطأ", f"حدث خطأ أثناء حفظ القسط: {error}")
                
        except ValueError:
            UIHelper.show_warning(self, "تنبيه", "يرجى إدخال مبلغ صحيح")

    def clear_installment_form(self):
        """مسح نموذج الأقساط"""
        self.car_select.setCurrentIndex(-1)
        self.client_select.setCurrentIndex(-1)
        self.installment_amount.clear()
        self.installments_count.setValue(1)
        self.start_date.setDate(QDate.currentDate())

    def update_installment_amount(self):
        """تحديث مبلغ القسط بناءً على المدخلات"""
        try:
            total = float(self.total_amount.text())
            down_payment = float(self.down_payment.text()) if self.down_payment.text() else 0
            count = self.installments_count.value()
            
            if total > 0 and count > 0:
                installment_amount = (total - down_payment) / count
                self.installment_amount.setText(f"{installment_amount:,.2f}")
            else:
                self.installment_amount.clear()
        except ValueError:
            self.installment_amount.clear()

    def load_installments(self):
        """تحميل الأقساط"""
        installments = self.installments_manager.get_installments()
        self.installments_table.setRowCount(len(installments))
        
        for i, installment in enumerate(installments):
            car, client, amount, count, start_date, status = installment
            
            self.installments_table.setItem(i, 0, QTableWidgetItem(car))
            self.installments_table.setItem(i, 1, QTableWidgetItem(client))
            self.installments_table.setItem(i, 2, QTableWidgetItem(f"{amount:,.2f}"))
            self.installments_table.setItem(i, 3, QTableWidgetItem(str(count)))
            self.installments_table.setItem(i, 4, QTableWidgetItem(start_date))
            self.installments_table.setItem(i, 5, QTableWidgetItem(status))
            
            color = {
                'متأخر': '#fff3cd',
                'جاري': '#d1e7dd',
                'منتهي': '#e2e3e5'
            }.get(status, '#ffffff')
            
            for j in range(6):
                self.installments_table.item(i, j).setBackground(QColor(color))

    def export_report(self):
        """تصدير التقرير إلى Excel"""
        if self.report_table.rowCount() == 0:
            UIHelper.show_warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ التقرير",
            "",
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if file_path:
            if not file_path.lower().endswith('.xlsx'):
                file_path += '.xlsx'
                
            headers = []
            for j in range(self.report_table.columnCount()):
                headers.append(self.report_table.horizontalHeaderItem(j).text())
                
            data = []
            for i in range(self.report_table.rowCount()):
                row = []
                for j in range(self.report_table.columnCount()):
                    item = self.report_table.item(i, j)
                    row.append(item.text() if item else "")
                data.append(row)
                
            success, error = self.reports_manager.export_to_excel(data, headers, file_path)
            
            if success:
                UIHelper.show_success(
                    self,
                    "نجاح",
                    f"تم تصدير التقرير بنجاح إلى:\n{file_path}"
                )
            else:
                UIHelper.show_error(
                    self,
                    "خطأ",
                    f"حدث خطأ أثناء تصدير البيانات: {error}"
                )

    def load_cars(self):
        """تحميل قائمة السيارات"""
        try:
            self.database.cursor.execute("""
                SELECT id, brand, model, chassis
                FROM cars
                ORDER BY id DESC
            """)
            cars = self.database.cursor.fetchall()
            
            # تنظيف القوائم أولاً
            if self.car_select is not None:
                self.car_select.clear()
            if self.invoice_car is not None:
                self.invoice_car.clear()
            
            # إضافة السيارات
            for car in cars:
                car_text = f"{car[1]} {car[2]} - {car[3]}"
                if self.car_select is not None:
                    self.car_select.addItem(car_text, car[0])
                if self.invoice_car is not None:
                    self.invoice_car.addItem(car_text, car[0])
                
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"خطأ في تحميل السيارات: {str(e)}")

    def load_clients(self):
        """تحميل قائمة العملاء"""
        try:
            self.database.cursor.execute("""
                SELECT id, name, phone
                FROM clients
                ORDER BY name
            """)
            clients = self.database.cursor.fetchall()
            
            # تنظيف القوائم أولاً
            if self.client_select is not None:
                self.client_select.clear()
            if self.invoice_client is not None:
                self.invoice_client.clear()
            
            # إضافة العملاء
            for client in clients:
                client_text = f"{client[1]} - {client[2]}"
                if self.client_select is not None:
                    self.client_select.addItem(client_text, client[0])
                if self.invoice_client is not None:
                    self.invoice_client.addItem(client_text, client[0])
                
        except Exception as e:
            UIHelper.show_error(self, "خطأ", f"خطأ في تحميل العملاء: {str(e)}")
