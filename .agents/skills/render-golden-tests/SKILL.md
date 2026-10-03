---
name: render-golden-tests
description: Implementa e audita render determinístico com Pillow e regressão visual para crop, EXIF, alpha, DPI, pan/zoom/rotação e naming. Use quando o bitmap final puder mudar.
---
# Render & Golden Tests

1. Use fixture sintética com grade, números, setas e cantos identificáveis.
2. Corrija EXIF antes de calcular dimensão/crop.
3. Renderize com DPI fixo e verifique dimensões exatas do canvas.
4. Teste `cover`, pan, zoom e rotação em posições extremas.
5. Cubra EXIF Orientation 1/3/6/8.
6. Para overlay RGBA, verifique alpha nas bordas e ausência de halo.
7. Use PNG determinístico para golden quando precisar igualdade estrita; para JPEG compare dimensões e tolerâncias visuais/pixels, não hash bruto entre plataformas.
8. Verifique que input nunca é sobrescrito e colisão gera nome novo.
9. Quando política ICC/metadata for definida, adicione teste explícito; até lá não invente transformação de perfil.
