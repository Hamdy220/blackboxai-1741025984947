@@ -5,13 +5,14 @@
     version="1.0.0",
     packages=find_packages(),
     install_requires=[
         'PyQt6>=6.0.0',
-        'pandas>=1.0.0'
+        'pandas>=1.0.0',
+        'openpyxl>=3.0.0'  # لدعم تصدير ملفات Excel
     ],
     entry_points={
         'console_scripts': [
             'car_dealership=car_dealership.main:main',
         ],
     },
     python_requires='>=3.6',
-)
+)
\ No newline at end of file