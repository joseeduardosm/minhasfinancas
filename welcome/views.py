"""Views de dashboard e calendario do app welcome."""

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone

from finance.models import Transacao, TransacaoExcecao
from finance.services import gerar_dados_mensais, mes_anterior, mes_posterior


def _resolver_ano_mes(request):
    """Le parametros de query e aplica fallback para o mes vigente."""
    hoje = timezone.localdate()
    year = request.GET.get("year", hoje.year)
    month = request.GET.get("month", hoje.month)

    try:
        year = int(year)
    except (TypeError, ValueError):
        year = hoje.year

    try:
        month = int(month)
    except (TypeError, ValueError):
        month = hoje.month

    year = max(1900, min(2100, year))
    month = max(1, min(12, month))
    return year, month


def _resolver_ano_mes_post_get(request):
    """Le ano/mes com prioridade para POST e fallback em GET/data atual."""
    hoje = timezone.localdate()
    year_raw = request.POST.get("year", request.GET.get("year", hoje.year))
    month_raw = request.POST.get("month", request.GET.get("month", hoje.month))

    try:
        year = int(year_raw)
    except (TypeError, ValueError):
        year = hoje.year

    try:
        month = int(month_raw)
    except (TypeError, ValueError):
        month = hoje.month

    year = max(1900, min(2100, year))
    month = max(1, min(12, month))
    return year, month


def _resolver_next_url(request, fallback_url: str) -> str:
    """Retorna URL de retorno segura para redirecionamentos de formularios."""
    next_url = request.POST.get("next", request.GET.get("next", "")).strip()
    if not next_url:
        return fallback_url
    if not next_url.startswith("/"):
        return fallback_url
    if not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return fallback_url
    return next_url


def _parse_date_yyyy_mm_dd(valor: str):
    """Converte texto YYYY-MM-DD em date ou None."""
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _resolver_data_ocorrencia(request, year: int, month: int):
    """Resolve data da ocorrencia alvo para acoes pontuais de recorrencia."""
    data_raw = request.POST.get("occurrence_date", request.GET.get("occurrence_date", "")).strip()
    data_obj = _parse_date_yyyy_mm_dd(data_raw)
    if data_obj:
        return data_obj

    day_raw = request.POST.get("day", request.GET.get("day", "")).strip()
    try:
        day = int(day_raw)
        return datetime(year, month, day).date()
    except (TypeError, ValueError):
        return None


def _build_contexto_mensal(request, incluir_dia=False):
    """Monta contexto comum para dashboard e calendario mensal."""
    year, month = _resolver_ano_mes(request)
    dados = gerar_dados_mensais(request.user, year, month)

    prev_year, prev_month = mes_anterior(year, month)
    next_year, next_month = mes_posterior(year, month)

    contexto = {
        "dados": dados,
        "month": month,
        "year": year,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    }

    if incluir_dia:
        selected_day = request.GET.get("day", "")
        contexto["selected_day"] = selected_day

    return contexto


@login_required
def home(request):
    """Dashboard mensal com grafico de receitas/despesas e saldo."""
    return render(request, "welcome/dashboard.html", _build_contexto_mensal(request))


@login_required
def calendario(request):
    """Pagina de calendario mensal com eventos financeiros."""
    return render(
        request,
        "welcome/calendar.html",
        _build_contexto_mensal(request, incluir_dia=True),
    )


@login_required
def api_mes(request):
    """Endpoint JSON para dados mensais do grafico e calendario."""
    year, month = _resolver_ano_mes(request)
    dados = gerar_dados_mensais(request.user, year, month)
    return JsonResponse(dados)


@login_required
def listar_eventos_tipo(request, tipo_slug):
    """Lista eventos do mes por tipo (receita/despesa), com busca e ordenacao."""
    year, month = _resolver_ano_mes(request)
    tipo_map = {"receita": Transacao.Tipo.RECEITA, "despesa": Transacao.Tipo.DESPESA}
    tipo = tipo_map.get(tipo_slug.lower())
    if not tipo:
        messages.error(request, "Tipo de listagem invalido.")
        return redirect(f"/welcome/?year={year}&month={month}")

    dados = gerar_dados_mensais(request.user, year, month)
    eventos = [evento for evento in dados["eventos"] if evento["tipo"] == tipo]

    eventos_normalizados = []
    for evento in eventos:
        data_obj = datetime.strptime(evento["data"], "%Y-%m-%d").date()
        valor_decimal = Decimal(str(evento["valor"]))
        eventos_normalizados.append(
            {
                **evento,
                "data_obj": data_obj,
                "data_br": data_obj.strftime("%d/%m/%Y"),
                "valor_brl": f"R$ {str(valor_decimal.quantize(Decimal('0.01'))).replace('.', ',')}",
            }
        )

    q = request.GET.get("q", "").strip()
    if q:
        q_lower = q.lower()

        def _match(evento):
            valor_str = f"{evento['valor']:.2f}"
            valor_pt = valor_str.replace(".", ",")
            return (
                q_lower in evento["nome"].lower()
                or q_lower in evento["data"]
                or q_lower in evento["data_br"].lower()
                or q_lower in valor_str.lower()
                or q_lower in valor_pt.lower()
            )

        eventos_normalizados = [evento for evento in eventos_normalizados if _match(evento)]

    sort = request.GET.get("sort", "data").strip().lower()
    direction = request.GET.get("dir", "asc").strip().lower()
    reverse = direction == "desc"
    if sort not in {"data", "nome", "valor"}:
        sort = "data"

    if sort == "nome":
        eventos_normalizados.sort(key=lambda item: item["nome"].lower(), reverse=reverse)
    elif sort == "valor":
        eventos_normalizados.sort(key=lambda item: item["valor"], reverse=reverse)
    else:
        eventos_normalizados.sort(key=lambda item: item["data_obj"], reverse=reverse)

    prev_year, prev_month = mes_anterior(year, month)
    next_year, next_month = mes_posterior(year, month)

    contexto = {
        "year": year,
        "month": month,
        "dias_no_mes": dados["dias_no_mes"],
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "tipo": tipo,
        "tipo_slug": tipo_slug.lower(),
        "titulo_tipo": "Receitas" if tipo == Transacao.Tipo.RECEITA else "Despesas",
        "eventos": eventos_normalizados,
        "q": q,
        "sort": sort,
        "dir": direction,
        "current_path": request.get_full_path(),
    }
    return render(request, "welcome/event_list.html", contexto)


@login_required
def lancar_transacao(request):
    """Recebe formulario da dashboard e cria lancamento de receita/despesa."""
    if request.method != "POST":
        return redirect("welcome:home")

    year, month = _resolver_ano_mes_post_get(request)

    tipo = request.POST.get("tipo", "").strip().upper()
    nome = request.POST.get("nome", "").strip()
    status = request.POST.get("status", "").strip().upper()
    recorrencia = request.POST.get("recorrencia", "").strip().upper()
    is_recorrente = request.POST.get("is_recorrente", "").strip().lower() in {"1", "true", "on", "yes"}
    data_base = request.POST.get("data_base", "").strip()
    data_fim_recorrencia = request.POST.get("data_fim_recorrencia", "").strip()
    valor_raw = request.POST.get("valor", "").strip().replace(",", ".")

    erros = []

    if tipo not in {Transacao.Tipo.RECEITA, Transacao.Tipo.DESPESA}:
        erros.append("Tipo de lancamento invalido.")
    if status not in {Transacao.Status.PLANEJADO, Transacao.Status.EXECUTADO}:
        erros.append("Status de lancamento invalido.")
    if is_recorrente and recorrencia not in {choice[0] for choice in Transacao.Recorrencia.choices}:
        erros.append("Recorrencia invalida.")
    if not nome:
        erros.append("Nome e obrigatorio.")

    try:
        valor = Decimal(valor_raw)
        if valor <= 0:
            erros.append("Valor deve ser maior que zero.")
    except (InvalidOperation, TypeError):
        erros.append("Valor monetario invalido.")
        valor = Decimal("0")

    data_base_obj = _parse_date_yyyy_mm_dd(data_base)
    if data_base_obj is None:
        erros.append("Data base invalida.")
    if is_recorrente:
        data_fim_obj = _parse_date_yyyy_mm_dd(data_fim_recorrencia)
        if data_fim_obj is None:
            erros.append("Data fim da recorrencia invalida.")
        elif data_base_obj and data_fim_obj < data_base_obj:
            erros.append("Data fim da recorrencia deve ser maior ou igual a data base.")
    else:
        data_fim_obj = data_base_obj
        recorrencia = Transacao.Recorrencia.MENSAL

    if erros:
        for erro in erros:
            messages.error(request, erro)
        fallback_error = f"/welcome/?year={year}&month={month}"
        return redirect(_resolver_next_url(request, fallback_error))

    Transacao.objects.create(
        usuario=request.user,
        tipo=tipo,
        status=status,
        nome=nome,
        valor=valor,
        data_base=data_base_obj,
        data_fim_recorrencia=data_fim_obj,
        recorrencia=recorrencia,
        ativo=True,
    )

    if data_base_obj.month != month or data_base_obj.year != year:
        messages.info(
            request,
            f"Lancamento salvo em {data_base_obj.month:02d}/{data_base_obj.year}. Exibindo esse mes.",
        )

    messages.success(request, "Lancamento salvo com sucesso.")
    fallback_url = f"/welcome/?year={data_base_obj.year}&month={data_base_obj.month}"
    return redirect(_resolver_next_url(request, fallback_url))


@login_required
def executar_transacao(request, transacao_id):
    """Marca transacao como executada e retorna para o calendario do mes."""
    if request.method != "POST":
        return redirect("welcome:home")

    year, month = _resolver_ano_mes_post_get(request)
    day = request.POST.get("day", request.GET.get("day", ""))
    transacao = get_object_or_404(Transacao, pk=transacao_id, usuario=request.user, ativo=True)

    if transacao.status != Transacao.Status.EXECUTADO:
        transacao.status = Transacao.Status.EXECUTADO
        transacao.save(update_fields=["status", "updated_at"])
        messages.success(request, "Lancamento marcado como executado.")
    else:
        messages.info(request, "Esse lancamento ja estava executado.")

    query = f"/welcome/calendario/?year={year}&month={month}"
    if day:
        query += f"&day={day}"
    return redirect(_resolver_next_url(request, query))


@login_required
def editar_transacao(request, transacao_id):
    """Tela de edicao de transacao financeira a partir do calendario."""
    transacao = get_object_or_404(Transacao, pk=transacao_id, usuario=request.user, ativo=True)
    year, month = _resolver_ano_mes_post_get(request)
    day = request.POST.get("day", request.GET.get("day", ""))
    ocorrencia_alvo = _resolver_data_ocorrencia(request, year, month) or transacao.data_base

    fallback_url = f"/welcome/calendario/?year={year}&month={month}"
    if day:
        fallback_url += f"&day={day}"
    next_url = _resolver_next_url(request, fallback_url)

    if request.method == "POST":
        tipo = request.POST.get("tipo", "").strip().upper()
        nome = request.POST.get("nome", "").strip()
        status = request.POST.get("status", "").strip().upper()
        recorrencia = request.POST.get("recorrencia", "").strip().upper()
        is_recorrente = request.POST.get("is_recorrente", "").strip().lower() in {"1", "true", "on", "yes"}
        data_base = request.POST.get("data_base", "").strip()
        data_fim_recorrencia = request.POST.get("data_fim_recorrencia", "").strip()
        valor_raw = request.POST.get("valor", "").strip().replace(",", ".")

        erros = []

        if tipo not in {Transacao.Tipo.RECEITA, Transacao.Tipo.DESPESA}:
            erros.append("Tipo de lancamento invalido.")
        if status not in {Transacao.Status.PLANEJADO, Transacao.Status.EXECUTADO}:
            erros.append("Status de lancamento invalido.")
        if is_recorrente and recorrencia not in {choice[0] for choice in Transacao.Recorrencia.choices}:
            erros.append("Recorrencia invalida.")
        if not nome:
            erros.append("Nome e obrigatorio.")

        try:
            valor = Decimal(valor_raw)
            if valor <= 0:
                erros.append("Valor deve ser maior que zero.")
        except (InvalidOperation, TypeError):
            erros.append("Valor monetario invalido.")
            valor = Decimal("0")

        data_base_obj = _parse_date_yyyy_mm_dd(data_base)
        if data_base_obj is None:
            erros.append("Data base invalida.")
        if is_recorrente:
            data_fim_obj = _parse_date_yyyy_mm_dd(data_fim_recorrencia)
            if data_fim_obj is None:
                erros.append("Data fim da recorrencia invalida.")
            elif data_base_obj and data_fim_obj < data_base_obj:
                erros.append("Data fim da recorrencia deve ser maior ou igual a data base.")
        else:
            data_fim_obj = data_base_obj
            recorrencia = Transacao.Recorrencia.MENSAL

        if erros:
            for erro in erros:
                messages.error(request, erro)
        else:
            transacao.tipo = tipo
            transacao.nome = nome
            transacao.status = status
            transacao.recorrencia = recorrencia
            transacao.data_base = data_base_obj
            transacao.data_fim_recorrencia = data_fim_obj
            transacao.valor = valor
            transacao.save()
            messages.success(request, "Lancamento atualizado com sucesso.")
            fallback_edit = (
                f"/welcome/calendario/?year={data_base_obj.year}&month={data_base_obj.month}&day={data_base_obj.day}"
            )
            return redirect(_resolver_next_url(request, fallback_edit))

    contexto = {
        "transacao": transacao,
        "year": year,
        "month": month,
        "day": day,
        "tipo_choices": Transacao.Tipo.choices,
        "status_choices": Transacao.Status.choices,
        "recorrencia_choices": Transacao.Recorrencia.choices,
        "next_url": next_url,
        "occurrence_date": ocorrencia_alvo.isoformat(),
        "is_recorrente": bool(
            transacao.data_fim_recorrencia
            and transacao.data_fim_recorrencia > transacao.data_base
        ),
    }
    return render(request, "welcome/edit_entry.html", contexto)


@login_required
def excluir_transacao(request, transacao_id):
    """Exclui (inativa) transacao e retorna para o calendario."""
    if request.method != "POST":
        return redirect("welcome:home")

    transacao = get_object_or_404(Transacao, pk=transacao_id, usuario=request.user, ativo=True)
    year, month = _resolver_ano_mes_post_get(request)
    day = request.POST.get("day", request.GET.get("day", "")).strip()
    scope = request.POST.get("delete_scope", "").strip().lower() or "all"
    occurrence_date = _resolver_data_ocorrencia(request, year, month)

    if scope not in {"one", "from", "all"}:
        scope = "all"

    if scope == "one":
        if occurrence_date is None:
            messages.error(request, "Nao foi possivel identificar a ocorrencia para exclusao.")
        else:
            TransacaoExcecao.objects.get_or_create(transacao=transacao, data=occurrence_date)
            messages.success(request, "Ocorrencia selecionada excluida com sucesso.")
    elif scope == "from":
        if occurrence_date is None:
            messages.error(request, "Nao foi possivel identificar a ocorrencia para exclusao em cadeia.")
        else:
            novo_fim = occurrence_date - timedelta(days=1)
            if novo_fim < transacao.data_base:
                transacao.ativo = False
                transacao.save(update_fields=["ativo", "updated_at"])
            else:
                transacao.data_fim_recorrencia = novo_fim
                transacao.save(update_fields=["data_fim_recorrencia", "updated_at"])
            messages.success(request, "Recorrencia ajustada a partir da data selecionada.")
    else:
        transacao.ativo = False
        transacao.save(update_fields=["ativo", "updated_at"])
        messages.success(request, "Lancamento excluido com sucesso.")

    query = f"/welcome/calendario/?year={year}&month={month}"
    if day:
        query += f"&day={day}"
    return redirect(_resolver_next_url(request, query))
