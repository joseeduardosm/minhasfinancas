# Minhas Financas

Projeto Django + MySQL para controle de financas pessoais.

## Regras da arquitetura atual

- Cada app possui HTML e CSS proprios.
- Nao existe compartilhamento de template/CSS entre apps diferentes.
- Codigo comentado para facilitar manutencao.

## Modulos iniciais

- `accounts`: login local e cadastro de novo usuario.
- `welcome`: dashboard, calendario e listagens de receitas/despesas.
- `finance`: modelo de transacoes, recorrencia e agregacoes mensais.

## Funcionalidades atuais

- Dashboard mensal com grafico (receitas x despesas) e navegacao entre meses.
- Calendario mensal de eventos financeiros.
- Listagem por tipo (`receita`/`despesa`) com:
  - ordenacao por data, nome e valor;
  - busca global no queryset do mes;
  - acoes por linha (executar, editar, excluir).
- Criacao de lancamento em modal (overlay) sem quebrar o fluxo da pagina.
- Edicao e exclusao com retorno para a tela de origem (`next`).

## Regras de recorrencia

- Todo evento nasce como **pontual**.
- O usuario so ativa recorrencia quando marca `Evento recorrente`.
- `Data fim da recorrencia` aparece apenas quando recorrencia esta ativa.
- Ao excluir evento recorrente, o usuario escolhe escopo:
  - apenas este evento;
  - deste evento em diante;
  - todos os relacionados.

## Modelos principais

- `finance.Transacao`
  - `usuario`, `tipo`, `status`, `nome`, `valor`, `data_base`
  - `recorrencia`, `data_fim_recorrencia`, `ativo`
- `finance.TransacaoExcecao`
  - usado para remover apenas uma ocorrencia dentro de uma serie recorrente.

## Como executar

1. Ativar ambiente virtual:

```bash
source .venv/bin/activate
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Rodar migracoes:

```bash
python manage.py migrate
```

4. Subir servidor local:

```bash
python manage.py runserver
```

## Testes

```bash
python manage.py test finance welcome --noinput
```
