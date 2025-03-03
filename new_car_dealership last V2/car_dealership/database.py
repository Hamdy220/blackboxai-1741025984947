import sqlite3
import os
import shutil
from pathlib import Path
from datetime import datetime
from .security import Security
from .audit_log import audit_logger

class Database:
    def __init__(self, db_name="aboraaya.db"):
        """تهيئة قاعدة البيانات"""
        # تحديد مسار قاعدة البيانات
        self.db_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.db_dir, db_name)
        
        # إنشاء المجلدات الضرورية
        self.contracts_dir = os.path.join(os.path.dirname(self.db_path), 'contracts')
        self.backups_dir = os.path.join(os.path.dirname(self.db_path), 'backups')
        os.makedirs(self.contracts_dir, exist_ok=True)
        os.makedirs(self.backups_dir, exist_ok=True)
        
        # تهيئة متغيرات الاتصال
        self.conn = None
        self.cursor = None
        
        # الاتصال بقاعدة البيانات
        db_exists = os.path.exists(self.db_path)
        self.connect()
        
        # إنشاء الجداول إذا لم تكن موجودة
        self.create_tables()
        
        # إضافة المستخدمين الافتراضيين إذا كانت قاعدة البيانات جديدة
        if not db_exists:
            self.create_default_users()

    def connect(self):
        """إنشاء اتصال جديد بقاعدة البيانات"""
        try:
            if self.conn is None or self.cursor is None:
                self.conn = sqlite3.connect(self.db_path)
                self.cursor = self.conn.cursor()
        except Exception as e:
            print(f"Error connecting to database: {str(e)}")
            raise

    def ensure_connection(self):
        """التأكد من وجود اتصال نشط بقاعدة البيانات"""
        try:
            # محاولة تنفيذ استعلام بسيط للتحقق من الاتصال
            self.cursor.execute("SELECT 1")
        except (sqlite3.OperationalError, sqlite3.ProgrammingError, AttributeError):
            # إعادة الاتصال إذا كان مغلقاً
            self.connect()

    def create_tables(self):
        """إنشاء جداول قاعدة البيانات"""
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                last_login TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                active INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE,
                address TEXT NOT NULL,
                status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                chassis TEXT NOT NULL UNIQUE,
                engine TEXT NOT NULL UNIQUE,
                condition TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                price REAL NOT NULL,
                purchase_date TEXT NOT NULL,
                license_expiry TEXT NOT NULL,
                contract_filename TEXT,
                contract_upload_date TEXT,
                client_name TEXT NOT NULL,
                client_phone TEXT NOT NULL,
                client_address TEXT NOT NULL,
                client_status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                related_to_car INTEGER DEFAULT 0,
                car_engine TEXT,
                FOREIGN KEY(car_engine) REFERENCES cars(engine)
            );

            -- جداول النظام المالي
            CREATE TABLE IF NOT EXISTS financial_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_type TEXT NOT NULL,  -- إيراد/مصروف
                category TEXT NOT NULL,     -- فئة الإيراد/المصروف
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY(created_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS installments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,    -- إجمالي مبلغ التقسيط
                paid_amount REAL DEFAULT 0,    -- المبلغ المدفوع
                remaining_amount REAL,         -- المبلغ المتبقي
                installment_count INTEGER,     -- عدد الأقساط
                start_date TEXT NOT NULL,      -- تاريخ بداية التقسيط
                next_payment_date TEXT,        -- تاريخ القسط القادم
                status TEXT NOT NULL,          -- حالة التقسيط (جاري، منتهي، متأخر)
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY(car_id) REFERENCES cars(id),
                FOREIGN KEY(client_id) REFERENCES clients(id),
                FOREIGN KEY(created_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS installment_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                installment_id INTEGER NOT NULL,
                payment_date TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT NOT NULL,  -- نقدي، شيك، تحويل بنكي
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY(installment_id) REFERENCES installments(id),
                FOREIGN KEY(created_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,  -- رقم الفاتورة المميز
                car_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                invoice_date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                payment_method TEXT NOT NULL,  -- نقدي، تقسيط
                payment_status TEXT NOT NULL,  -- مدفوع، غير مدفوع، تقسيط
                notes TEXT,
                file_path TEXT,               -- مسار ملف الفاتورة PDF
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY(car_id) REFERENCES cars(id),
                FOREIGN KEY(client_id) REFERENCES clients(id),
                FOREIGN KEY(created_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id)
            );
        """)
        self.conn.commit()

    def create_default_users(self):
        """إنشاء المستخدمين الافتراضيين"""
        default_users = [
            ('admin', 'admin123', 'مدير'),
            ('sales', 'sales123', 'موظف_مبيعات'),
            ('accountant', 'accountant123', 'محاسب')
        ]
        
        for username, password, role in default_users:
            hashed_password = Security.hash_password(password)
            self.cursor.execute("""
                INSERT OR IGNORE INTO users (username, password, role, active)
                VALUES (?, ?, ?, 1)
            """, (username, hashed_password, role))
        
        self.conn.commit()

    def verify_login(self, username, password):
        """التحقق من صحة بيانات تسجيل الدخول"""
        try:
            self.cursor.execute("""
                SELECT id, password, role, username 
                FROM users 
                WHERE username = ? AND active = 1
            """, (username,))
            
            user = self.cursor.fetchone()
            if not user:
                return None
                
            user_id, stored_password, role, username = user
            
            if Security.verify_password(password, stored_password):
                # تحديث آخر تسجيل دخول
                self.cursor.execute("""
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (user_id,))
                self.conn.commit()
                
                # تسجيل حدث تسجيل الدخول
                audit_logger.log_event(
                    user_id=user_id,
                    username=username,
                    event_type="تسجيل_دخول",
                    description="تم تسجيل الدخول بنجاح"
                )
                
                return user_id, role, username
            else:
                # تسجيل محاولة تسجيل دخول فاشلة
                audit_logger.log_event(
                    user_id=user_id,
                    username=username,
                    event_type="تسجيل_دخول",
                    description="محاولة تسجيل دخول فاشلة - كلمة مرور خاطئة",
                    status="فشل"
                )
                return None
                
        except sqlite3.Error as e:
            print(f"خطأ في التحقق من تسجيل الدخول: {str(e)}")
            return None

    def create_backup(self):
        """إنشاء نسخة احتياطية من قاعدة البيانات"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(
                self.backups_dir,
                f'aboraaya_backup_{timestamp}.db'
            )
            
            # إغلاق الاتصال مؤقتاً
            self.conn.close()
            
            # نسخ الملف
            shutil.copy2(self.db_path, backup_path)
            
            # إعادة فتح الاتصال
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            return True, backup_path
            
        except Exception as e:
            error_msg = f"فشل في إنشاء نسخة احتياطية: {str(e)}"
            print(error_msg)
            return False, error_msg

    def get_contract_path(self, contract_filename):
        """الحصول على المسار الكامل لملف العقد"""
        if not contract_filename:
            return None
        return os.path.join(self.contracts_dir, contract_filename)

    def add_car(self, car_data, user_id, username):
        """إضافة سيارة جديدة"""
        try:
            # استخراج اسم ملف العقد من البيانات
            contract_filename = car_data[10]
            contract_upload_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if contract_filename else None

            # إنشاء سجل جديد للسيارة
            self.cursor.execute("""
                INSERT INTO cars (
                    brand, model, year, chassis, engine,
                    condition, transaction_type, price,
                    purchase_date, license_expiry,
                    contract_filename, contract_upload_date,
                    client_name, client_phone, client_address,
                    client_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*car_data[:10], contract_filename, contract_upload_date, *car_data[11:]))
            
            car_id = self.cursor.lastrowid
            self.conn.commit()

            # تسجيل الحدث
            audit_logger.log_event(
                user_id=user_id,
                username=username,
                event_type="إضافة_سيارة",
                description=f"تمت إضافة سيارة جديدة: {car_data[0]} {car_data[1]}"
            )
            
            return True
            
        except sqlite3.IntegrityError as e:
            print(f"Error adding car: {str(e)}")
            return False

    def update_car_contract(self, car_id, contract_filename, user_id, username):
        """تحديث معلومات عقد السيارة"""
        try:
            contract_upload_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.cursor.execute("""
                UPDATE cars 
                SET contract_filename = ?,
                    contract_upload_date = ?
                WHERE id = ?
            """, (contract_filename, contract_upload_date, car_id))
            
            self.conn.commit()

            # تسجيل الحدث
            audit_logger.log_event(
                user_id=user_id,
                username=username,
                event_type="تحديث_عقد",
                description=f"تم تحديث عقد السيارة رقم {car_id}"
            )
            
            return True
        except Exception as e:
            print(f"Error updating car contract: {str(e)}")
            return False

    def add_client(self, client_data, user_id, username):
        """إضافة أو تحديث بيانات العميل"""
        try:
            name, phone, address, status = client_data
            
            # محاولة تحديث العميل إذا كان موجود
            self.cursor.execute("""
                UPDATE clients 
                SET name = ?, address = ?, status = ?
                WHERE phone = ?
            """, (name, address, status, phone))
            
            # إذا لم يتم تحديث أي صف (العميل غير موجود)، قم بإضافته
            if self.cursor.rowcount == 0:
                self.cursor.execute("""
                    INSERT INTO clients (name, phone, address, status)
                    VALUES (?, ?, ?, ?)
                """, (name, phone, address, status))
                
                # تسجيل حدث الإضافة
                audit_logger.log_event(
                    user_id=user_id,
                    username=username,
                    event_type="إضافة_عميل",
                    description=f"تمت إضافة عميل جديد: {name}"
                )
            else:
                # تسجيل حدث التحديث
                audit_logger.log_event(
                    user_id=user_id,
                    username=username,
                    event_type="تحديث_عميل",
                    description=f"تم تحديث بيانات العميل: {name}"
                )
            
            self.conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Error in add_client: {str(e)}")
            return False

    def add_transaction(self, transaction_data, user_id, username):
        """إضافة معاملة جديدة"""
        try:
            self.cursor.execute("""
                INSERT INTO transactions (
                    type, name, date, amount,
                    related_to_car, car_engine
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, transaction_data)
            
            transaction_id = self.cursor.lastrowid
            self.conn.commit()

            # تسجيل الحدث
            audit_logger.log_event(
                user_id=user_id,
                username=username,
                event_type="إضافة_معاملة",
                description=f"تمت إضافة معاملة جديدة: {transaction_data[1]}"
            )
            
            return True
        except sqlite3.IntegrityError:
            return False

    def close(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            finally:
                self.conn = None
                self.cursor = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
