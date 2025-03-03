from PyQt6.QtWidgets import QMessageBox

class UIHelper:
    @staticmethod
    def show_success(parent, title, message):
        """Show success message dialog"""
        QMessageBox.information(parent, title, message)

    @staticmethod
    def show_error(parent, title, message):
        """Show error message dialog"""
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def show_warning(parent, title, message):
        """Show warning message dialog"""
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def confirm_action(parent, title, message):
        """Show confirmation dialog and return True if user confirms"""
        reply = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
