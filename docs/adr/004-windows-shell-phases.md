# ADR-004 — Integração Windows em duas fases

**Status:** Aceito

## Decisão
V1 usa shell verb clássico/registro e aceita “Mostrar mais opções” no Windows 11. Menu moderno por `IExplorerCommand` + sparse MSIX só será avaliado após o MVP.

## Motivo
Reduz complexidade de COM, signing e deployment enquanto valida o fluxo real do operador.
