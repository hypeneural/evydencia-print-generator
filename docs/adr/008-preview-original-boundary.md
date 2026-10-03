# ADR-008 — Preview proxy no editor, original no renderer

**Status:** Aceito

## Contexto
JPEGs de câmera de ~8 MB expandem muito quando decodificados. Repetir originais em múltiplos slots aumenta memória e prejudica drag/zoom.

## Decisão
O ingest gera um preview/proxy local deduplicado, usado pelo Fabric. O SourceAsset mantém referência ao original. O renderer reabre o original ao gerar o arquivo final.

## Consequências
- melhor responsividade;
- uma source pode alimentar muitos slots sem N decodes;
- preview nunca é output de produção;
- preview/render parity precisa de testes;
- cache local exige invalidação/cleanup.
