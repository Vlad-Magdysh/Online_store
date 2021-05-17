import re
from email_validator import validate_email, EmailNotValidError


class Validate:
    @staticmethod
    def name(user_name: str):
        user_name = user_name.strip()
        if re.match(r"\b[A-Z][a-z]+$", user_name):
            return True

    @staticmethod
    def mail_index(mail_index: str):
        if re.match(r"\d{5}", mail_index):
            return True

    @staticmethod
    def phone(phone: str):
        user_phone = phone.strip()
        if re.match(r"\+\d{12}", user_phone):
            return True

    @staticmethod
    def email(email: str):
        try:
            validate_email(email)
        except EmailNotValidError as er:
            return False
        else:
            return True

    @staticmethod
    def password(password: str):
        user_password = password.strip()
        if re.match(r'[A-Za-z0-9@#$%^&+=]{8,}', user_password):
            return True



