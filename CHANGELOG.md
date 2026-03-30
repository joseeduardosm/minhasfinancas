# Changelog

## 2026-03-30

### Adicionado
- Campo `data_fim_recorrencia` em `Transacao`.
- Modelo `TransacaoExcecao` para exclusao pontual de ocorrencias recorrentes.
- Modal de criacao de lancamento na listagem por tipo.
- Script `recorrencia_toggle.js` para exibir campos de recorrencia sob demanda.
- Script `delete_scope.js` para escolher escopo de exclusao de recorrencia.
- Registro admin de `TransacaoExcecao`.

### Alterado
- Evento agora e pontual por padrao; recorrencia so e aplicada quando usuario marca a opcao.
- `Data fim da recorrencia` passou a ser obrigatoria apenas quando recorrencia esta ativa.
- Exclusao de evento recorrente ganhou escopos:
  - apenas este evento;
  - deste evento em diante;
  - todos os relacionados.
- Servicos mensais passaram a respeitar `data_fim_recorrencia` e excecoes de ocorrencia.
- README atualizado com fluxo funcional atual e regras de recorrencia.

### Testes
- Suite `finance + welcome` atualizada e validada (`14 testes OK`).
