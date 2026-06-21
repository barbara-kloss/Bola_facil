from services.whatsapp_service import WhatsAppService


class NotificationService:
    @staticmethod
    def notify_new_game(users, game):
        message = f"Novo jogo no BolãoFácil: {game['home_team']} x {game['away_team']}."
        return NotificationService._notify_users(users, message)

    @staticmethod
    def notify_result(users, game):
        message = (
            f"Resultado lançado: {game['home_team']} {game['home_score']} x "
            f"{game['away_score']} {game['away_team']}."
        )
        return NotificationService._notify_users(users, message)

    @staticmethod
    def notify_pending_bet(users, game):
        message = f"Não esqueça seu palpite: {game['home_team']} x {game['away_team']}."
        return NotificationService._notify_users(users, message)

    @staticmethod
    def _notify_users(users, message):
        results = []
        for user in users:
            phone = user["whatsapp_phone"] if isinstance(user, dict) else user.whatsapp_phone
            if phone:
                results.append(WhatsAppService.send_message(phone, message))
        return results
