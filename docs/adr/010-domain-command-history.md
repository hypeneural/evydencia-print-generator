# ADR-010 — Undo/redo por comandos de domínio

**Status:** Aceito

## Contexto
Serializar o canvas Fabric inteiro ou pixels a cada pointermove é pesado, frágil e acopla history ao runtime visual.

## Decisão
History registra comandos/patches pequenos de Template/Job. Um gesto contínuo de drag, wheel ou slider é coalescido em uma única entrada ao finalizar.

## Consequências
- undo/redo determinístico;
- menos memória;
- Fabric pode ser reconstruído do estado;
- testes de history não dependem de bitmap.
