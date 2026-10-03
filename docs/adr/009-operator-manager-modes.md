# ADR-009 — Operador e Gestor são modos distintos

**Status:** Aceito

## Contexto
Layers, z-order e configuração física são úteis ao gestor, mas aumentam erro e carga cognitiva do operador.

## Decisão
O Operador edita conteúdo dentro de slots e usa ações de produto. O Gestor edita estrutura, layers, lock, visibility, grupos e publicação.

## Consequências
- toolbar do Operador permanece pequena;
- bring forward/send backward pertence ao Gestor;
- objetos protegidos não são editáveis no Operador;
- um mesmo canvas core suporta duas superfícies de controle.
