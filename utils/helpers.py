import re
from datetime import datetime


def is_valid_email(email):
    return bool(email and re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def is_valid_password(password):
    if not password or len(password) < 8:
        return False
    has_letter = bool(re.search(r"[a-zA-Z]", password))
    has_number = bool(re.search(r"\d", password))
    return has_letter and has_number


def is_valid_phone(phone):
    if not phone:
        return True # Optional field
    digits = re.sub(r"\D", "", phone)
    return 10 <= len(digits) <= 15


def format_phone(phone):
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return phone


def format_datetime(value):
    if not value:
        return ""
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value.strftime("%d/%m/%Y %H:%M")


def format_match_time(value):
    formatted = format_datetime(value)
    if not formatted:
        return {"date": "", "time": ""}
    date, time = formatted.split(" ")
    return {"date": date, "time": time}


def match_status_label(status, api_status=None):
    labels = {
        "scheduled": "AGENDADO",
        "live": "AO VIVO",
        "in_progress": "EM ANDAMENTO",
        "finished": "FINALIZADO",
        "cancelled": "CANCELADO",
        "timed": "AGENDADO",
        "ns": "NÃO INICIADO",
        "pst": "ADIADO",
        "canc": "CANCELADO",
    }
    # api_status pode vir como "TIMED", "NS", "PST", etc. — traduzir também
    if api_status:
        return labels.get(api_status.lower(), api_status)
    return labels.get(status, status.upper())
