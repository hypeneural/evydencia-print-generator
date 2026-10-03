# Security and Privacy

- Não versionar fotos reais de clientes, familiares ou crianças.
- V1 não envia imagens a serviços externos.
- Não persistir caminho completo de produção em logs normais.
- Argumentos do Explorer e templates importados são entrada não confiável.
- Validar existência, tipo real e limites antes de decodificar.
- Output nunca sobrescreve silenciosamente input.
- Preferir temporário + rename no mesmo volume.
- Nenhum processamento de imagem dentro de explorer.exe na V1.
- Installer remove somente as chaves que cria.
