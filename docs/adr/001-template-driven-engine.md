# ADR-001 — Motor dirigido por templates

**Status:** Aceito

## Contexto
Calendário, Chaveiro e Globo compartilham canvas, slots, fontes, transforms e output.

## Decisão
Manter um único motor. Diferenças de produto são expressas por Template; uma execução concreta é expressa por Job.

## Consequências
- novos produtos preferem dados a branches de engine;
- schemas são fronteiras de compatibilidade;
- exceções específicas exigem justificativa e ADR.
