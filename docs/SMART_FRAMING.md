# Smart Framing — Especificação Técnica e Arquitetura de Design

Este documento especifica a arquitetura, heurísticas geométricas, seleção de modelo e garantias de conformidade do recurso **Smart Framing** (Enquadramento Inteligente) para o **EVYDÊNCIA Print Generator**.

---

## 1. Contexto e Objetivos

No fluxo de produção fotográfica em loja física (gabaritos de Calendário, Globo de Neve e Chaveiro 3×4), o operador frequentemente recebe fotos casuais tiradas por smartphones com enquadramentos arbitrários (selfies, retratos distantes, fotos descentralizadas).

O **Smart Framing** tem como objetivo:
1. **Calcular automaticamente uma proposta de `SlotTransform`** (`scale`, `translation_x`, `translation_y`, `rotation=0`) que posicione o rosto ou grupo de pessoas de forma harmônica na abertura física do slot.
2. **Eliminar o esforço repetitivo de ajuste manual** pelo operador na maioria das fotos padrão.
3. **Manter a soberania do operador**: o enquadramento sugerido é apenas um ponto de partida não-destrutivo; o operador pode ajustar zoom com scroll do mouse e pan por arrasto a qualquer momento.
4. **Garantir privacidade estrita (LGPD/GDPR)**: zero armazenamento de dados biométricos.

---

## 2. Princípios de Clean-Room

- **Independência Total**: O design aqui especificado foi concebido a partir de primeiros princípios e literatura aberta de visão computacional.
- **Zero Dependência Proprietária**: Não há reutilização de código, heurísticas fechadas ou pesos originários de projetos externos como `paleta-do-bruxo-audit`.
- **Apenas Bibliotecas Abertas e Permissivas**: Modelos e runtimes com licenças MIT ou Apache 2.0.

---

## 3. Seleção de Modelo e Runtime

### 3.1 Modelo Selecionado: OpenCV YuNet (`cv2.FaceDetectorYN`)

- **Arquivo**: `face_detection_yunet_2023mar.onnx`
- **Tamanho dos Pesos**: ~330 KB (ultraleve, embarcável no pacote ou assets).
- **Licença**: MIT.
- **Runtime**: Integrado nativamente no `opencv-python` via DNN module (`cv2.FaceDetectorYN.create`).
- **Latência no CPU**: 15–25 ms para resolução 640×480 em CPUs Intel Core i3/i5 de 8ª+ geração.
- **Saídas**:
  - Bounding box facial: $[x, y, w, h]$;
  - Confiança da detecção: score entre $0.0$ e $1.0$;
  - 5 pontos de marcos faciais (landmarks): olho direito, olho esquerdo, ponta do nariz, canto direito da boca, canto esquerdo da boca.

### 3.2 Análise Comparativa de Alternativas

| Critério | OpenCV YuNet | Google MediaPipe | RetinaFace / InsightFace |
| :--- | :--- | :--- | :--- |
| **Tamanho dos Pesos** | **~330 KB** | ~3–10 MB | >30 MB |
| **Dependências Python** | Apenas `opencv-python` (já presente) | `mediapipe` (pesado, conflito protobuf) | `torch` ou `onnxruntime` pesados |
| **Latência CPU** | **15–25 ms** | 20–40 ms | 80–200 ms |
| **Licenciamento** | **MIT** | Apache 2.0 | Não-comercial / restritivo |
| **Complexidade de Empacotamento PyInstaller** | **Trivial** | Alta (problemas com binários C++) | Alta |

---

## 4. Heurísticas e Algoritmo de Enquadramento

### 4.1 Pré-processamento e Escalonamento
Para manter a latência abaixo de 30 ms, a imagem de entrada $I$ com dimensões $(W_{\text{orig}}, H_{\text{orig}})$ é redimensionada proporcionalmente para que sua dimensão máxima seja de 640 px antes da inferência no YuNet. As coordenadas resultantes são então mapeadas de volta para o espaço original da imagem multiplicando pelo fator de escala correspondente.

### 4.2 Invariante de Cobertura Física (Cover Invariant)
Qualquer enquadramento gerado **DEVE** satisfazer a invariante de cobertura:
$$\text{scale} \ge \text{scale}_{\min} = \max\left(\frac{W_{\text{slot}}}{W_{\text{orig}}}, \frac{H_{\text{slot}}}{H_{\text{orig}}}\right)$$
Isso garante matematicamente que nenhum pixel em branco ou vazio apareça na abertura do slot.

### 4.3 Caso A: Sujeito Único (Retrato / 3×4 / Chaveiro / Globo)

Quando um único rosto é detectado com confiança $\ge 0.60$:
1. **Linha dos Olhos (Eye-Line)**:
   - A altura dos olhos $Y_{\text{eyes}} = \frac{Y_{\text{right\_eye}} + Y_{\text{left\_eye}}}{2}$ deve ser posicionada entre **35% e 42%** do topo da abertura física do slot.
   - Para fotos 3×4 (Chaveiro), a norma padrão exige os olhos a aproximadamente 38% do topo.
2. **Proporção da Cabeça (Headroom / Head Scale)**:
   - A altura da cabeça $H_{\text{face}}$ deve ocupar entre **50% e 65%** da altura do slot $H_{\text{slot}}$ (em produtos 3×4, recomenda-se ~65% para garantir enquadramento padrão de documento).
   - O fator de escala sugerido é calculado para acomodar essa proporção, com clamping para nunca ser menor que $\text{scale}_{\min}$.
3. **Centralização Horizontal**:
   - O ponto médio entre os olhos $X_{\text{eyes\_center}}$ é alinhado horizontalmente com o centro do slot ($0.5 \times W_{\text{slot}}$).
4. **Garantia de Limites**:
   - As translações calculadas $(\text{translation}_x, \text{translation}_y)$ sofrem clamp para garantir que as bordas da imagem cubram completamente o retângulo do slot.

### 4.4 Caso B: Múltiplos Sujeitos (Foto de Família / Casal / Grupo)

Quando dois ou mais rostos são detectados com confiança $\ge 0.60$:
1. **Bounding Box de União**:
   $$B_{\text{group}} = [X_{\min}, Y_{\min}, X_{\max}, Y_{\max}]$$
   englobando todos os rostos detectados.
2. **Margem de Segurança (Padding)**:
   - Adiciona-se uma margem de segurança de 20% ao redor de $B_{\text{group}}$ para incluir cabelo, ombros e respiro.
3. **Enquadramento do Grupo**:
   - A escala é definida para que a caixa com margem caiba integralmente no slot.
   - Caso a escala resultante seja menor que $\text{scale}_{\min}$, aplica-se $\text{scale}_{\min}$ e centraliza-se o centróide do grupo no slot.
   - A translação horizontal e vertical é ajustada para centralizar o centróide de $B_{\text{group}}$, respeitando os limites da imagem.

### 4.5 Caso C: Fallback e Flag `SMART_FRAME_NEEDS_REVIEW`

Se nenhum rosto for detectado ou a pontuação de confiança for menor que $0.60$ (ex.: fotos de pets, paisagens, objetos ou faces excessivamente ocluídas):
1. **Fallback Automático**: Aplica o enquadramento geométrico padrão de centro com cobertura mínima:
   $$\text{scale} = \text{scale}_{\min}, \quad \text{translation}_x = 0, \quad \text{translation}_y = 0$$
2. **Sinalização Não-Bloqueante**: O slot recebe o status `SMART_FRAME_NEEDS_REVIEW`.
3. **Experiência do Operador**: A UI exibe um indicador sutil (ícone/aviso no card do slot) alertando que o enquadramento automático não encontrou faces claras, permitindo ao operador ajustar manualmente o enquadramento com facilidade. A geração do arquivo nunca é bloqueada por esse status.

---

## 5. Arquitetura de Pipeline e Desempenho

### 5.1 Execução Assíncrona em Segundo Plano (Background Worker)
- **Zero Bloqueio da UI**: O processamento do Smart Framing é offloaded para um `ThreadPoolExecutor` no backend Python.
- **Preview Imediato**: Ao selecionar ou arrastar uma foto para o slot, o editor exibe imediatamente o preview com enquadramento de centro padrão (`scale = scale_min`).
- **Atualização Suave**: Quando o worker do Smart Framing conclui o cálculo (normalmente em < 30 ms), ele despacha uma mensagem via IPC (`bridge`) com o `SlotTransform` sugerido, atualizando a cena Fabric.js de forma transparente.

```
+---------------+     drop image      +-----------------+
|  Operador /   | ------------------> |   UI (Fabric)   |
|  File Drop    |                     | (instant cover) |
+---------------+                     +-----------------+
                                               |
                                               | ingest_paths (IPC)
                                               v
                                      +-----------------+
                                      | Python Backend  |
                                      | (Thread Worker) |
                                      +-----------------+
                                               |
                                               | YuNet inference (15-25ms)
                                               v
                                      +-----------------+
                                      | Heurística mm   |
                                      | -> SlotTransform|
                                      +-----------------+
                                               |
                                               | event: smart_frame_ready
                                               v
                                      +-----------------+
                                      |   UI (Fabric)   |
                                      | (smooth update) |
                                      +-----------------+
```

### 5.2 Contrato com o `EditState`
O Smart Framing gera uma instância comum de `SlotTransform`:
```json
{
  "scale": 1.25,
  "translation_x": -35.0,
  "translation_y": -12.5,
  "rotation": 0
}
```
Não há formato proprietário. O operador pode livremente alterar a escala com a roda do mouse (`wheel`) ou a posição com clique e arrasto, gravando estados no histórico de `undo/redo`.

---

## 6. Conformidade e Privacidade (LGPD / GDPR)

A proteção da privacidade dos clientes em quiosques e lojas de revelação é mandatória:

1. **Natureza Estritamente Efêmera**: As imagens e tensores de detecção residem apenas em memória RAM durante o ciclo de cálculo (<50 ms).
2. **Zero Reconhecimento Facial / Biometria**: O sistema **NÃO** calcula embeddings faciais, vetores biométricos, identificadores faciais ou hashes de reconhecimento. Ele atua exclusivamente como detector de localização de caixa e marcos angulares para alinhamento geométrico.
3. **Zero Persistência em Disco de Dados Faciais**: Nenhum dado de marcos faciais ou coordenadas de faces é gravado em logs, arquivos temporários ou metadados de jobs.
4. **Conformidade com a LGPD (Lei 13.709/2018, Art. 11)**: Por não realizar identificação pessoal automatizada nem armazenamento de biometria, o sistema opera estritamente dentro da finalidade técnica de processamento gráfico autorizado pelo usuário final.

---

## 7. Fases de Rollout

- **PR #20 (Atual)**: Apenas esta especificação técnica e arquitetura de design (`docs/SMART_FRAMING.md`). Zero código de inteligência artificial ou modelos incluídos.
- **Próxima Feature Branch**: Implementação do módulo `evydencia_print_generator.smart_framing`, downloads dos pesos do YuNet e testes unitários com fixtures sintéticas, **somente após a aprovação visual completa (VISUAL PASS) do PR #20**.
