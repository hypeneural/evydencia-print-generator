# Matriz de Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Preview divergir do render | Alto | transformações normalizadas + golden tests |
| Medidas físicas incorretas | Alto | mm canônico + draft/production + prova física |
| EXIF inesperado | Alto | transpose antes da geometria |
| Área vazia no slot | Médio | cover_required + clamp |
| Foto real no Git | Alto | regras, checker, fixtures sintéticas |
| Contexto Antigravity excessivo | Médio | root curto + regras por diretório + Skills |
| Customization inválida | Alto | validator CI |
| Editor genérico excessivo | Médio | Fabric direto; upstreams como referência |
| Shell afetar Explorer | Alto | V1 shell verb externo |
| Unicode/quoting quebrar launch | Alto | contrato CLI + testes Windows |
| Repo público expor código/asset | Médio | nenhuma foto/segredo; avaliar private |
