# ADR-007 — Explorer só lança o aplicativo

**Status:** Aceito

## Decisão
Nenhuma decodificação/render de imagens roda dentro de `explorer.exe` na V1. O handler apenas lança `EvydenciaPrintGenerator.exe` com argumentos.

## Consequências
Falhas do renderer/app não devem derrubar o Explorer; testes do shell ficam focados em registro, quoting e launch.
