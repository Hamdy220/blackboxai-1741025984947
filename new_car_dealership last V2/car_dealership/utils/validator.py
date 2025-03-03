import re

class Validator:
    @staticmethod
    def validate_phone(phone):
        """التحقق من صحة رقم الهاتف المصري."""
        pattern = r'^01[0125][0-9]{8}$'
        return bool(re.match(pattern, phone))

    @staticmethod
    def validate_price(price):
        """التحقق من صحة السعر."""
        try:
            float_price = float(price)
            return float_price > 0
        except ValueError:
            return False

    @staticmethod
    def validate_year(year):
        """التحقق من صحة سنة صنع السيارة."""
        try:
            int_year = int(year)
            return 1900 <= int_year <= 2024
        except ValueError:
            return False

    @staticmethod
    def validate_chassis(chassis):
        """التحقق من صحة رقم الشاسيه."""
        return bool(chassis and len(chassis) >= 5)

    @staticmethod
    def validate_engine(engine):
        """التحقق من صحة رقم المحرك."""
        return bool(engine and len(engine) >= 5)
