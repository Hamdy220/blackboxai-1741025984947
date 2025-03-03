import os
import logging
from datetime import datetime
from pathlib import Path

class AuditLog:
    def __init__(self):
        """تهيئة نظام تسجيل الأحداث"""
        # إنشاء مجلد السجلات إذا لم يكن موجوداً
        self.logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # تهيئة ملف السجل
        self.log_file = os.path.join(self.logs_dir, 'audit.log')
        
        # إعداد التسجيل
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger('audit')

    def log_event(self, user_id: int, username: str, event_type: str, description: str, status: str = "نجاح"):
        """
        تسجيل حدث في السجل
        
        Args:
            user_id (int): معرف المستخدم
            username (str): اسم المستخدم
            event_type (str): نوع الحدث
            description (str): وصف الحدث
            status (str): حالة الحدث (نجاح/فشل)
        """
        try:
            log_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': user_id,
                'username': username,
                'event_type': event_type,
                'description': description,
                'status': status
            }
            
            log_message = (
                f"المستخدم: {username} (ID: {user_id}) | "
                f"النوع: {event_type} | "
                f"الوصف: {description} | "
                f"الحالة: {status}"
            )
            
            self.logger.info(log_message)
            
        except Exception as e:
            error_message = f"خطأ في تسجيل الحدث: {str(e)}"
            self.logger.error(error_message)
            raise Exception(error_message)

    def get_logs(self, limit: int = None, event_type: str = None, user_id: int = None) -> list:
        """
        استرجاع سجلات الأحداث مع إمكانية التصفية
        
        Args:
            limit (int): عدد السجلات المطلوبة (اختياري)
            event_type (str): نوع الحدث للتصفية (اختياري)
            user_id (int): معرف المستخدم للتصفية (اختياري)
            
        Returns:
            list: قائمة بالسجلات المطلوبة
        """
        try:
            if not os.path.exists(self.log_file):
                return []
                
            with open(self.log_file, 'r', encoding='utf-8') as f:
                logs = f.readlines()
            
            # تصفية السجلات
            filtered_logs = []
            for log in logs:
                if event_type and event_type not in log:
                    continue
                if user_id and str(user_id) not in log:
                    continue
                filtered_logs.append(log.strip())
            
            # تحديد عدد السجلات المطلوبة
            if limit:
                filtered_logs = filtered_logs[-limit:]
                
            return filtered_logs
            
        except Exception as e:
            error_message = f"خطأ في استرجاع السجلات: {str(e)}"
            self.logger.error(error_message)
            return []

    def clear_logs(self):
        """مسح جميع السجلات (متاح فقط للمدير)"""
        try:
            if os.path.exists(self.log_file):
                # إغلاق جميع handlers للسماح بتعديل الملف
                for handler in self.logger.handlers[:]:
                    handler.close()
                    self.logger.removeHandler(handler)
                logging.shutdown()
                
                # إنشاء مجلد للنسخ الاحتياطية إذا لم يكن موجوداً
                backup_dir = os.path.join(os.path.dirname(self.logs_dir), 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                
                # إنشاء نسخة احتياطية قبل المسح
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_base = os.path.join(backup_dir, timestamp)
                
                # نسخ ملف السجلات
                log_backup = f"{backup_base}_audit.log.backup"
                os.rename(self.log_file, log_backup)
                
                # نسخ قاعدة البيانات
                db_file = os.path.join(os.path.dirname(__file__), 'aboraaya.db')
                if os.path.exists(db_file):
                    db_backup = f"{backup_base}_database.db.backup"
                    import shutil
                    shutil.copy2(db_file, db_backup)
                
                # إنشاء ملف سجل جديد
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.write(f"# تم إنشاء ملف سجل جديد في {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                # إعادة تهيئة التسجيل
                logging.basicConfig(
                    filename=self.log_file,
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    force=True
                )
                self.logger = logging.getLogger('audit')
                
                return True, f"تم مسح السجلات وإنشاء نسخة احتياطية كاملة في: {backup_dir}"
            return False, "ملف السجل غير موجود"
            
        except Exception as e:
            error_message = f"خطأ في مسح السجلات: {str(e)}"
            self.logger.error(error_message)
            return False, error_message

    def restore_backup(self, backup_file: str):
        """استرجاع نسخة احتياطية من السجلات"""
        try:
            if not os.path.exists(backup_file):
                return False, "ملف النسخة الاحتياطية غير موجود"

            # إغلاق جميع handlers للسماح بتعديل الملف
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)
            logging.shutdown()

            # استخراج المسار الأساسي للنسخة الاحتياطية
            backup_base = backup_file.rsplit('_audit.log.backup', 1)[0]
            db_backup = f"{backup_base}_database.db.backup"

            # عمل نسخة احتياطية من الملفات الحالية
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            current_backup_dir = os.path.join(os.path.dirname(self.logs_dir), 'backups', f'current_{timestamp}')
            os.makedirs(current_backup_dir, exist_ok=True)

            # نسخ الملفات الحالية كنسخة احتياطية
            if os.path.exists(self.log_file):
                current_log_backup = os.path.join(current_backup_dir, 'audit.log.backup')
                os.rename(self.log_file, current_log_backup)

            db_file = os.path.join(os.path.dirname(__file__), 'aboraaya.db')
            if os.path.exists(db_file):
                current_db_backup = os.path.join(current_backup_dir, 'database.db.backup')
                import shutil
                shutil.copy2(db_file, current_db_backup)

            # استرجاع النسخة الاحتياطية
            # 1. استرجاع ملف السجلات
            with open(backup_file, 'r', encoding='utf-8') as src, \
                 open(self.log_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())

            # 2. استرجاع قاعدة البيانات إذا كانت موجودة
            if os.path.exists(db_backup):
                import shutil
                shutil.copy2(db_backup, db_file)

            # إعادة تهيئة التسجيل
            logging.basicConfig(
                filename=self.log_file,
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                force=True
            )
            self.logger = logging.getLogger('audit')

            return True, "تم استرجاع النسخة الاحتياطية بنجاح"

        except Exception as e:
            error_message = f"خطأ في استرجاع النسخة الاحتياطية: {str(e)}"
            if hasattr(self, 'logger'):
                self.logger.error(error_message)
            return False, error_message

# إنشاء نسخة عامة من AuditLog للاستخدام في جميع أنحاء التطبيق
audit_logger = AuditLog()
