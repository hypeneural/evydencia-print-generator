# Performance Budgets

Estes são **targets de engenharia**, não promessas. A primeira implementação deve medir baseline numa máquina Windows do estúdio e ajustar budgets com evidência.

## Cenário de referência
- Windows 11;
- JPEGs ~8 MB;
- até 18 slots no Chaveiro;
- 1–9 sources comuns;
- viewport 1366×768 e 1920×1080.

## Targets
| Operação | Target inicial |
|---|---:|
| janela utilizável após launch | <= 2.5 s cold |
| source aceita → thumbnail/preview | p95 <= 1.0 s por source comum |
| click/toolbar feedback | < 100 ms |
| drag/zoom | 60 fps ideal; não sustentar < 30 fps |
| undo/redo | perceptivelmente imediato |
| trocar source já em cache | < 150 ms visual |
| UI durante render final | responsiva, sem freeze |

## Guardrails
- Fabric recebe preview, não original.
- Preview padrão: longest side 2048 px.
- Source repetida reutiliza preview/decode.
- Não gerar preview por slot.
- Não persistir pixels no history.
- Events de alta frequência usam requestAnimationFrame/coalescing.
- React não recebe setState global por pointermove.
- Viewport zoom contínuo não é requisito do MVP.
- Canvas/Fabric cache global não é alterado sem profile.

## Benchmark obrigatório
Guardar em relatório:
- CPU/RAM;
- display scale/DPR;
- arquivos e dimensões;
- slots/sources;
- cold/warm cache;
- p50/p95;
- heap/process memory antes/depois;
- flamegraph/Performance recording quando houver jank.

## Gate
Uma feature que piora drag/zoom ou source load de forma relevante precisa explicar o custo e ter alternativa antes do merge.
