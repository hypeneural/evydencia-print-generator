# Architecture

## Objetivo
Uma única engine deve suportar produtos diferentes por dados, sem branches de lógica específicos por produto.

## Fronteiras

### Template
Contrato persistente de produto:
- canvas físico;
- slots;
- grupos;
- overlay;
- permissões;
- output;
- provenance/status.

### Job
Contrato de uma execução:
- template/version;
- fontes locais;
- slot→fonte;
- pan/zoom/rotação normalizados.

### UI — React/Fabric.js
Responsável por preview/interação. Não é fonte de verdade para geometria física nem export final. Nunca persistir JSON bruto do Fabric como contrato público.

### Desktop/Renderer — Python/Pillow
Responsável por:
1. carregar original;
2. corrigir EXIF;
3. resolver mm→px;
4. aplicar cover + Job;
5. clip por slot;
6. alpha-composite do overlay;
7. salvar output collision-safe.

### Windows
Explorer apenas inicia `EvydenciaPrintGenerator.exe <path>`. A V1 não carrega código de processamento dentro de explorer.exe.

## Dependências
Direção permitida:
`Windows shell -> app controller -> Template/Job -> renderer`
`UI -> bridge de domínio -> Template/Job`

UI e shell não conhecem detalhes internos do renderer.

## Estado
V1 não exige backend, banco ou internet. Templates são arquivos versionados no pacote/repo.
