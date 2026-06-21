"""
API Response Messages
Mensagens padronizadas para respostas de API com feedback claro para o usuário
"""

class ApiMessages:
    """Mensagens padronizadas para diferentes tipos de operações"""

    # Autenticação
    AUTH_LOGIN_SUCCESS = "Bem-vindo! Você foi autenticado com sucesso."
    AUTH_LOGIN_ERROR = "E-mail ou senha incorretos. Tente novamente."
    AUTH_REGISTER_SUCCESS = "Conta criada com sucesso! Você já pode fazer login."
    AUTH_REGISTER_ERROR = "Não foi possível criar a conta. Verifique os dados e tente novamente."
    AUTH_LOGOUT_SUCCESS = "Você saiu com sucesso."

    # Jogos
    GAME_CREATE_SUCCESS = "Jogo criado com sucesso!"
    GAME_CREATE_ERROR = "Não foi possível criar o jogo. Verifique os dados e tente novamente."
    GAME_UPDATE_SUCCESS = "Jogo atualizado com sucesso!"
    GAME_UPDATE_ERROR = "Não foi possível atualizar o jogo. Tente novamente."
    GAME_DELETE_SUCCESS = "Jogo removido com sucesso!"
    GAME_DELETE_ERROR = "Não foi possível remover o jogo. Tente novamente."
    GAME_NOT_FOUND = "Jogo não encontrado."
    GAME_RESULT_RECORDED = "Resultado do jogo registrado com sucesso!"
    GAME_RESULT_ERROR = "Não foi possível registrar o resultado. Tente novamente."
    GAME_SYNC_SUCCESS = "Jogos sincronizados com sucesso!"
    GAME_SYNC_ERROR = "Erro ao sincronizar jogos. Tente novamente mais tarde."
    GAME_SYNC_PROGRESS = "Sincronizando jogos do Brasileirão..."

    # Palpites
    BET_CREATE_SUCCESS = "Palpite registrado com sucesso!"
    BET_CREATE_ERROR = "Não foi possível registrar seu palpite. Tente novamente."
    BET_UPDATE_SUCCESS = "Palpite atualizado com sucesso!"
    BET_UPDATE_ERROR = "Não foi possível atualizar seu palpite. Tente novamente."
    BET_DELETE_SUCCESS = "Palpite removido com sucesso!"
    BET_DELETE_ERROR = "Não foi possível remover seu palpite. Tente novamente."
    BET_NOT_FOUND = "Palpite não encontrado."
    BET_CLOSED = "Não é possível fazer palpites após o jogo ter iniciado."
    BET_INVALID = "Palpite inválido. Verifique os dados e tente novamente."

    # Ranking/Pontuação
    RANKING_UPDATED = "Ranking atualizado!"
    SCORING_CALCULATED = "Pontuação calculada com sucesso!"
    SCORING_ERROR = "Erro ao calcular a pontuação. Tente novamente."

    # Chat/Mensagens
    MESSAGE_SENT = "Mensagem enviada com sucesso!"
    MESSAGE_ERROR = "Não foi possível enviar a mensagem. Tente novamente."

    # Validação de entrada
    VALIDATION_REQUIRED_FIELD = "Este campo é obrigatório."
    VALIDATION_INVALID_EMAIL = "E-mail inválido."
    VALIDATION_INVALID_DATE = "Data inválida."
    VALIDATION_INVALID_SCORE = "Placar inválido."

    # Erros genéricos
    ERROR_GENERIC = "Ocorreu um erro. Tente novamente."
    ERROR_NETWORK = "Erro de conexão. Verifique sua internet e tente novamente."
    ERROR_TIMEOUT = "A solicitação demorou muito. Tente novamente."
    ERROR_UNAUTHORIZED = "Você não tem permissão para realizar esta ação."
    ERROR_FORBIDDEN = "Acesso negado."
    ERROR_NOT_FOUND = "Recurso não encontrado."
    ERROR_CONFLICT = "Conflito ao processar a solicitação."
    ERROR_VALIDATION = "Dados inválidos. Verifique e tente novamente."

    # Sucesso genérico
    SUCCESS_GENERIC = "Operação realizada com sucesso!"


def get_message(message_key, **kwargs):
    """
    Obtém uma mensagem do dicionário, com suporte a formatação.
    
    Uso:
        get_message('GAME_CREATE_SUCCESS')
        get_message('ERROR_VALIDATION', field='email')
    """
    try:
        message = getattr(ApiMessages, message_key, ApiMessages.ERROR_GENERIC)
        return message.format(**kwargs) if kwargs else message
    except (KeyError, IndexError, AttributeError):
        return ApiMessages.ERROR_GENERIC
