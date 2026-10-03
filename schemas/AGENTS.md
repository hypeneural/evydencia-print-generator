# Schema Rules

- Schemas são contratos entre UI, renderer, templates e jobs.
- Mudança incompatível exige schema_version, ADR e migração.
- additionalProperties deve ser restritivo quando possível.
- Validações semânticas vivem também em scripts/testes.
- Não enfraquecer schema para acomodar dado incorreto; mantenha draft.
