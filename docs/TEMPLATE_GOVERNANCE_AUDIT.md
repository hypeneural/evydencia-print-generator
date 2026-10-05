# Relatório de Auditoria de Governança de Templates

**Data:** 2026-10-05  
**Escopo:** `templates/calendario-2027`, `templates/chaveiro-3x4`, `templates/globo-neve`, `templates/polaroid-natal`  
**Status do Gate G7 (Physical Production Geometry):** **`PENDING`**

---

## 1. Resumo Executivo

Esta auditoria forense mapeia e reconcilia as divergências entre a definição dos arquivos `template.json`, o código do motor de renderização, e a documentação histórica em `PRODUCT_SPECS.md` e `EDITOR_UX.md`.

Nenhum template é automaticamente despromovido nesta etapa para evitar regressões nas rotinas de testes existentes, mas o sistema passa a expor semanticamente o status `draft` na interface do Operador e a manter o Gate G7 estritamente em **`PENDING`** até que as provas físicas reais sejam realizadas.

---

## 2. Auditoria Individual por Template

### 2.1. Calendário 2027 (`calendario-2027`)
- **Status Atual no JSON:** `production` (`template_version: 1.0.0`)
- **Origem dos Dados:**
  - Asset: `templates/calendario-2027/assets/overlay-2027.png` (`1067 × 1474 px`, RGBA).
  - Resolução: `254 DPI` medido no Photoshop sobre o asset original fornecido pelo estúdio.
  - Folha física: `106.7 × 147.4 mm` (derivada da resolução nominal de 254 DPI).
  - Abertura de foto: janela transparente `alpha = 0` medida em `left=119, top=108, width=821, height=393 px` (`11.9 × 10.8 mm` no espaço físico).
- **Conflitos Documentais Auditados:**
  - `PRODUCT_SPECS.md` continha menções legadas a um metadado EXIF de 72 DPI e afirmava que as dimensões físicas em centímetros e o DPI final ainda estavam pendentes.
- **Classificação Forense:**
  - `MEASURED:` Janela transparente (821×393 px) e resolução (254 DPI) medidas em Photoshop.
  - `DERIVED:` Dimensões físicas em mm calculadas a partir de 254 DPI.
  - `CONFIRMED:` Composição em tela e renderização digital aprovadas.
  - `PENDING:` Prova física impressa em papel fotográfico de laboratório.
  - `CONFLICTING_DOCUMENTATION:` Reconciliado (documentação histórica atualizada).

---

### 2.2. Chaveiro 3x4 (`chaveiro-3x4`)
- **Status Atual no JSON:** `production` (`template_version: 1.0.0`)
- **Origem dos Dados:**
  - Folha física: `216 × 152 mm` @ `300 DPI` (`2551 × 1795 px`).
  - Slots: 18 slots de `34 × 44 mm` dispostos em grade 6 colunas × 3 linhas.
  - Composição: Fundo branco gerado pelo renderer sem máscara de overlay decorativa.
  - Margens: Grade centralizada com margens laterais de 6 mm e margens verticais de 10 mm.
- **Conflitos Documentais Auditados:**
  - A nota do `template.json` afirmava historicamente: *"Ação de preenchimento em lote preenche toda a folha com a mesma foto"*. Essa descrição ficou obsoleta após a introdução da ação "Preencher restantes", multi-drop nativo do Windows Explorer e duplicação em lote com wrap-around.
  - `PRODUCT_SPECS.md` continha itens pendentes quanto à orientação do arquivo para o laboratório e pareamento frente/verso.
- **Classificação Forense:**
  - `MEASURED:` Dimensões da folha (216×152 mm) e do chaveiro (34×44 mm).
  - `DERIVED:` Centralização da grade na folha fotográfica.
  - `CONFIRMED:` Composição digital e renderização parcial ($\ge 2$ slots).
  - `PENDING:` Prova de corte físico e alinhamento com a guilhotina mecânica do laboratório.
  - `CONFLICTING_DOCUMENTATION:` Reconciliado (notas do template e especificações atualizadas).

---

### 2.3. Globo de Neve (`globo-neve`)
- **Status Atual no JSON:** `production` (`template_version: 1.1.0`)
- **Origem dos Dados:**
  - Folha física: `152 × 102 mm` @ `300 DPI` (`1795 × 1205 px`, 10×15 cm fotográfico canônico).
  - Slots: 2 slots de `50 × 80 mm` dispostos lado a lado.
  - Layout: Assimétrico, derivado de fotografia com escala de régua do gabarito físico real do laboratório (`foto_1` em x=16.7, y=10.2; `foto_2` em x=73.7, y=10.2; gap de 7 mm entre fotos; margem direita de 28.3 mm).
- **Conflitos Documentais Auditados:**
  - O campo `provenance.pending` estava vazio, mas o campo `notes` continha: *"Pendente confirmação vetorial numérica via arquivo CorelDRAW / gabarito oficial do laboratório"*.
- **Classificação Forense:**
  - `MEASURED:` Folha 152×102 mm e fotos 50×80 mm.
  - `DERIVED:` Coordenadas extraídas de fotografia de referência do laboratório.
  - `CONFIRMED:` Proporção e enquadramento visual estáveis.
  - `PENDING:` Arquivo vetorial nativo do CorelDRAW para homologação final.
  - `CONFLICTING_DOCUMENTATION:` Reconciliado (pendência documentada explicitamente).

---

### 2.4. Polaroid Natal (`polaroid-natal`)
- **Status Atual no JSON:** `draft` (`template_version: 1.0.0`)
- **Origem dos Dados:**
  - Asset: `templates/polaroid-natal/assets/polaroid-overlay.png` (`980 × 1205 px`, RGBA, SHA-256 `0586cfb00e21a7da170d135b351ed36a36f5c24e76b8e2fcb95a231df07dfdfc`).
  - Resolução: `300 DPI` nominal.
  - Folha física: `82.97 × 102.02 mm` (derivada de 980×1205 px a 300 DPI).
  - Slot `foto_principal`: janela transparente `alpha = 0` medida em `left=69, top=59, width=843, height=862 px` (`71.37 × 72.98 mm` em x=5.84, y=5.00 mm).
  - Overlay: Obrigatório com verificação fail-closed contra redimensionamentos destrutivos.
- **Conflitos Documentais Auditados:**
  - Documentação citava geração de hash no nome do arquivo; o código real gera `Polaroid_<nome>.jpg` com sufixo sequencial `_002` em caso de colisão.
- **Classificação Forense:**
  - `MEASURED:` Overlay e janela transparente delimitados com precisão pixel-perfect.
  - `DERIVED:` Dimensões físicas em mm a partir de 300 DPI.
  - `CONFIRMED:` Composição e validação fail-closed.
  - `PENDING:` Prova física impressa em papel fotográfico no laboratório.
  - `CONFLICTING_DOCUMENTATION:` Reconciliado.

---

## 3. Matriz Consolidada de Governança

| Template | Status Formal | Medição Pixels / mm | Validação Digital | Prova Física Laboratório | Risco Residual |
|---|:---:|:---:|:---:|:---:|---|
| **Calendário 2027** | `production` | Medido (Photoshop) | Aprovado | Pendente | Pequeno desvio de margem na prensa |
| **Chaveiro 3x4** | `production` | Medido (Gabarito) | Aprovado | Pendente | Alinhamento com faca de corte física |
| **Globo de Neve** | `production` | Derivado de foto | Aprovado | Pendente | Tolerância de montagem na cúpula |
| **Polaroid Natal** | `draft` | Medido (Pixel-perfect)| Aprovado | Pendente | Aguardando impressão teste do operador |

---

## 4. Diretrizes para a UX e o Release Industrial

1. **Exposição Clara de Rascunhos:**
   - Templates com `status === "draft"` exibem badge permanente `[Rascunho]` no seletor de produtos.
   - A interface exibe aviso claro: *"Template em validação física. Use este arquivo somente para prova."*
   - O botão principal de ação altera seu rótulo de *"Gerar arquivo de produção"* para *"Gerar arquivo de prova"*.
2. **Manutenção do Gate G7 em PENDING:**
   - O Gate G7 permanecerá classificado como `PENDING` em todos os relatórios até que as provas físicas de cada produto sejam impressas e aprovadas no ambiente real do laboratório.
3. **Working Color Space / ICC como Próximo Marco de Produção:**
   - O pipeline atual compõe em RGB sRGB implícito. Antes do release final, deve ser implementada a conversão explícita de perfis de cores ICC para garantir fidelidade cromática idêntica entre o monitor do operador e a impressora química do laboratório.
