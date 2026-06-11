"""
Testes para autenticação
"""

import unittest
from utils.helpers import validate_email, hash_password, verify_password

class TestAuth(unittest.TestCase):
    """Testes de autenticação"""
    
    def test_validate_email_valid(self):
        """Testa validação de email válido"""
        self.assertTrue(validate_email('usuario@example.com'))
    
    def test_validate_email_invalid(self):
        """Testa validação de email inválido"""
        self.assertFalse(validate_email('email_invalido'))
    
    def test_hash_password(self):
        """Testa hashing de senha"""
        password = "senha123"
        hashed = hash_password(password)
        self.assertIsNotNone(hashed)

if __name__ == '__main__':
    unittest.main()
