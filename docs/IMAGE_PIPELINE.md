# Image Pipeline

## Princípio
**Editar leve, renderizar original.**

Uma foto JPEG de ~8 MB pode decodificar para dezenas de MB em RAM. Colocar vários originais no browser/Fabric degrada abertura, drag e zoom. O editor usa preview proxy; Pillow reabre o original somente para o render final.

## Pipeline de ingest
```text
Explorer / File Dialog / Drag Drop
              │
              ▼
        Python IngestService
              │
      validate + stat + EXIF
              │
         SourceRegistry
       ┌──────┴────────┐
       │               │
 original path     preview job
                       │
                       ▼
                local preview cache
                       │
                       ▼
                    Fabric
```

## Source identity
V1:
`normalized path + size + mtime_ns`

Um hash completo é caro e não é necessário para o primeiro cache. Se o arquivo mudar, size/mtime invalida o preview. Hash pode ser adicionado para casos específicos depois de benchmark.

## Preview proxy
Target inicial:
- longest side 2048 px;
- EXIF aplicado;
- RGB/sRGB de tela conforme política;
- qualidade visual suficiente para crop;
- uma geração por source;
- URI local, sem transportar original em base64 pelo bridge.

O tamanho é configurável e deve ser benchmarkado em monitores HiDPI. Não subir acima por intuição.

## Original
- nunca é alterado;
- path existe apenas no runtime/local state;
- não é enviado para cloud;
- é reaberto no momento do render;
- metadata relevante é lida novamente se necessário.

## Render final
```text
Template + immutable Job snapshot
             │
             ▼
          original
             │
      EXIF transpose
             │
      color policy
             │
        cover/crop
             │
      pan/zoom/rotate
             │
           clip
             │
        overlay RGBA
             │
      encode once
             │
       temp + rename
```

## Qualidade
- geometria calculada em pixels somente a partir de mm+DPI;
- LANCZOS para resize final quando aplicável;
- JPEG padrão alvo quality 95; production subsampling/profile dependem de validação do laboratório;
- ICC nunca é descartado silenciosamente;
- output recebe DPI correto;
- evitar ciclos JPEG→JPEG intermediários.

## Background work
Preview generation e final render não podem travar o thread visual. Começar com fila pequena/thread pool e só adotar multiprocess se benchmark demonstrar necessidade.

## Cache
- cache local por source fingerprint;
- LRU/age cleanup;
- limite configurável;
- remover previews órfãos;
- nunca confundir cache com source original.
