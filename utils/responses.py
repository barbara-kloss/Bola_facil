"""
Utilitário centralizado para respostas de feedback (sucesso/erro).
Elimina duplicação de código nos controladores e garante consistência
entre respostas JSON (para chamadas fetch/AJAX) e flash messages (para
requisições de formulário tradicional).
"""
from flask import flash, jsonify, request, redirect, url_for


def respond(
    message: str,
    *,
    ok: bool = True,
    status: int = None,
    redirect_to: str = None,
    template_fn=None,
    template_kwargs: dict = None,
    data: dict = None,
):
    """
    Responde de forma inteligente com JSON ou redirect+flash dependendo do
    tipo da requisição.

    Parâmetros:
        message      – Texto da mensagem a ser exibido ao usuário.
        ok           – True = sucesso, False = erro.
        status       – Código HTTP. Se omitido: 200 para sucesso, 400 para erro.
        redirect_to  – Endpoint Flask (url_for) para redirecionar (apenas HTML).
        template_fn  – Callable que retorna render_template() para erros HTML.
        template_kwargs – Kwargs extras para template_fn.
        data         – Dados extras para incluir na resposta JSON.

    Exemplos:
        # Sucesso simples
        return respond("Jogo criado!", ok=True, redirect_to="games.list_games")

        # Erro com dados extras em JSON
        return respond("E-mail inválido.", ok=False, status=422,
                       template_fn=lambda: render_template("auth/register.html"))
    """
    if status is None:
        status = 200 if ok else 400

    category = "success" if ok else "error"

    if request.is_json:
        payload = {"message": message} if ok else {"error": message}
        if data:
            payload.update(data)
        return jsonify(payload), status

    # Resposta HTML
    flash(message, category)

    if ok:
        target = redirect_to or request.referrer or "/"
        # Se for um endpoint Flask, converte; senão trata como URL direta
        try:
            return redirect(url_for(target))
        except Exception:
            return redirect(target)

    # Erro HTML: rerenderiza o template ou redireciona
    if template_fn:
        kwargs = template_kwargs or {}
        return template_fn(**kwargs), status

    target = redirect_to or request.referrer or "/"
    try:
        return redirect(url_for(target))
    except Exception:
        return redirect(target)
