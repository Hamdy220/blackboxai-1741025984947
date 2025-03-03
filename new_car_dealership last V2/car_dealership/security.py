import bcrypt
import logging
from datetime import datetime

class Security:
    @staticmethod
    def hash_password(password: str) -> bytes:
        """
        تشفير كلمة المرور باستخدام bcrypt
        
        Args:
            password (str): كلمة المرور المراد تشفيرها
            
        Returns:
            bytes: كلمة المرور المشفرة
        """
        if isinstance(password, str):
            password = password.encode('utf-8')
        return bcrypt.hashpw(password, bcrypt.gensalt())

    @staticmethod
    def verify_password(password: str, hashed: bytes) -> bool:
        """
        التحقق من صحة كلمة المرور
        
        Args:
            password (str): كلمة المرور المدخلة
            hashed (bytes): كلمة المرور المشفرة المخزنة
            
        Returns:
            bool: True إذا كانت كلمة المرور صحيحة
        """
        if isinstance(password, str):
            password = password.encode('utf-8')
        if isinstance(hashed, str):
            hashed = hashed.encode('utf-8')
        try:
            return bcrypt.checkpw(password, hashed)
        except Exception as e:
            logging.error(f"خطأ في التحقق من كلمة المرور: {str(e)}")
            return False

    @staticmethod
    def get_user_permissions(role: str) -> dict:
        """
        الحصول على صلاحيات المستخدم بناءً على دوره
        
        Args:
            role (str): دور المستخدم (مدير، موظف مبيعات، محاسب)
            
        Returns:
            dict: قاموس يحتوي على الصلاحيات
        """
        permissions = {
            'مدير': {
                'إدارة_المستخدمين': True,
                'إدارة_السيارات': True,
                'إدارة_العملاء': True,
                'إدارة_المعاملات': True,
                'النسخ_الاحتياطي': True,
                'عرض_السجلات': True,
                'إدارة_العقود': True
            },
            'موظف_مبيعات': {
                'إدارة_المستخدمين': False,
                'إدارة_السيارات': True,
                'إدارة_العملاء': True,
                'إدارة_المعاملات': True,
                'النسخ_الاحتياطي': False,
                'عرض_السجلات': False,
                'إدارة_العقود': True
            },
            'محاسب': {
                'إدارة_المستخدمين': False,
                'إدارة_السيارات': False,
                'إدارة_العملاء': True,
                'إدارة_المعاملات': True,
                'النسخ_الاحتياطي': False,
                'عرض_السجلات': True,
                'إدارة_العقود': False
            }
        }
        return permissions.get(role, {})
