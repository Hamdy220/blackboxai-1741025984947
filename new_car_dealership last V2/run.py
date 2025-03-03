#!/usr/bin/env python3
"""
نظام إدارة معرض أبو ريا للسيارات
"""

import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QCoreApplication
from car_dealership.database import Database
from car_dealership.login import LoginWindow
from car_dealership.main import MainWindow
from car_dealership.audit_log import audit_logger

def setup_environment():
    """تهيئة بيئة التطبيق"""
    try:
        # إنشاء المجلدات الضرورية
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dirs = ['logs', 'backups', 'contracts']
        
        for dir_name in dirs:
            dir_path = os.path.join(base_dir, 'car_dealership', dir_name)
            os.makedirs(dir_path, exist_ok=True)
            print(f"تم إنشاء/التحقق من وجود المجلد: {dir_path}")
        
        return True
    except Exception as e:
        print(f"خطأ في تهيئة بيئة التطبيق: {str(e)}")
        return False

def main():
    """نقطة البداية الرئيسية للتطبيق"""
    try:
        # تهيئة بيئة التطبيق
        if not setup_environment():
            print("فشل في تهيئة بيئة التطبيق")
            return 1
        
        print("جاري بدء التطبيق...")
        
        # إنشاء تطبيق Qt
        app = QApplication(sys.argv)
        
        # تطبيق نمط RTL على التطبيق بأكمله
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar)
        app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        print("جاري تهيئة قاعدة البيانات...")
        
        # تهيئة قاعدة البيانات
        database = Database()
        
        print("جاري عرض نافذة تسجيل الدخول...")
        
        # عرض نافذة تسجيل الدخول
        login = LoginWindow(database)
        if login.exec() == 1:  # إذا نجح تسجيل الدخول
            # الحصول على معلومات المستخدم
            user_info = login.get_user_info()
            
            print(f"تم تسجيل الدخول بنجاح كـ {user_info['role']}")
            print("جاري تحميل النافذة الرئيسية...")
            
            # إنشاء النافذة الرئيسية مع تمرير معلومات المستخدم
            window = MainWindow(
                database=database,
                user_id=user_info['user_id'],
                username=user_info['username'],
                role=user_info['role']
            )
            
            # تسجيل بدء جلسة العمل
            audit_logger.log_event(
                user_id=user_info['user_id'],
                username=user_info['username'],
                event_type="بدء_جلسة",
                description=f"تم بدء جلسة عمل جديدة كـ {user_info['role']}"
            )
            
            print("تم تحميل النافذة الرئيسية بنجاح")
            window.showMaximized()  # عرض النافذة بحجم كامل
            
            # تشغيل حلقة الأحداث الرئيسية
            return app.exec()
            
        print("تم إلغاء تسجيل الدخول")
        return 0
        
    except Exception as e:
        print(f"خطأ غير متوقع: {str(e)}")
        import traceback
        traceback.print_exc()  # طباعة تفاصيل الخطأ كاملة
        return 1

if __name__ == "__main__":
    sys.exit(main())
