---
trigger: model_decision
description: "Aplica-se ao lidar com fotografias, fixtures, screenshots, logs, caminhos de arquivos, telemetria, exportação ou dados de produção."
---
# Privacy and File Safety

- Não adicionar fotos reais de clientes, familiares ou crianças ao Git, issues, PRs, screenshots ou golden tests.
- Não persistir caminho completo, nome de cliente ou metadata sensível em logs normais.
- V1 não envia imagens a serviços externos.
- Trate templates/imports e argumentos de shell como dados não confiáveis.
- Valide tipo real do arquivo, não apenas extensão.
- Outputs nunca sobrescrevem silenciosamente a origem.
- Qualquer telemetria futura deve ser local/opt-in e não conter pixels, metadata fotográfica ou caminhos completos.
