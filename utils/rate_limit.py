"""
Proteção básica contra força bruta para tentativas de login.
Usa cache em memória (dict thread-safe) — sem dependência extra.

Estratégia:
  - Após MAX_ATTEMPTS falhas consecutivas por IP, bloqueia por LOCKOUT_SECONDS.
  - Após um login bem-sucedido, o contador do IP é zerado.
"""
import threading
import time

MAX_ATTEMPTS = 5       # tentativas antes do bloqueio
LOCKOUT_SECONDS = 300  # 5 minutos

_lock = threading.Lock()
_store: dict[str, dict] = {}  # ip -> {"count": int, "locked_until": float}


def _get_ip() -> str:
    from flask import request
    # Respeita proxy reverso
    return (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.remote_addr
        or "unknown"
    )


def is_blocked() -> bool:
    """Retorna True se o IP atual estiver bloqueado por excesso de tentativas."""
    ip = _get_ip()
    with _lock:
        entry = _store.get(ip)
        if not entry:
            return False
        locked_until = entry.get("locked_until", 0)
        if locked_until and time.time() < locked_until:
            return True
        if locked_until and time.time() >= locked_until:
            # Desbloqueio automático
            _store.pop(ip, None)
        return False


def record_failure() -> int:
    """
    Registra uma tentativa de login falhada para o IP atual.
    Retorna o número de tentativas acumuladas.
    """
    ip = _get_ip()
    with _lock:
        entry = _store.setdefault(ip, {"count": 0, "locked_until": 0})
        entry["count"] += 1
        if entry["count"] >= MAX_ATTEMPTS:
            entry["locked_until"] = time.time() + LOCKOUT_SECONDS
        return entry["count"]


def record_success() -> None:
    """Limpa o contador de falhas para o IP atual após login bem-sucedido."""
    ip = _get_ip()
    with _lock:
        _store.pop(ip, None)


def remaining_lockout() -> int:
    """Retorna segundos restantes do bloqueio (0 se não estiver bloqueado)."""
    ip = _get_ip()
    with _lock:
        entry = _store.get(ip)
        if not entry:
            return 0
        locked_until = entry.get("locked_until", 0)
        remaining = int(locked_until - time.time())
        return max(remaining, 0)
