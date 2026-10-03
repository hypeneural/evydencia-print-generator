# ADR-002 — Milímetros como unidade canônica

**Status:** Aceito

## Decisão
Geometria física persistida em mm. Pixels são derivados no render usando DPI e uma função canônica.

`px = round(mm / 25.4 * dpi)`

## Consequências
- preview pode redimensionar sem alterar a verdade física;
- DPI pode variar sem reescrever templates;
- provas físicas devem validar medidas/offsets.
