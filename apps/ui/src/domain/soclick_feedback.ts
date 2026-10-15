/** Human-first operator messages for the local EvydFlow draft handoff.
 *
 * This module never requests the network and never suggests automatic retry.
 * Exported JPEG remains on disk even when the optional SóClick draft fails.
 */
export interface SoclickHandoffResult {
  ok: boolean;
  browser_opened?: boolean;
  panel_url?: string;
  is_existing?: boolean;
  error?: string;
  error_code?: string;
}

export interface SoclickNotice {
  type: "success" | "error";
  message: string;
  nextStep?: string;
  panelUrl?: string;
  code?: string;
}

/** When a request may have committed, an explicit panel check is required. */
export function requiresDraftReconciliation(result: SoclickHandoffResult): boolean {
  if (result.ok) return false;
  // Older Python bridges can omit error_code entirely; fail closed when they
  // cannot establish that the draft was rejected before creation.
  return ![
    "ROOTS_NOT_CONFIGURED",
    "OPERATOR_NOT_AUTHORIZED",
    "PANEL_OFFLINE",
    "RENDER_CHANGED",
    "HANDOFF_REJECTED",
  ].includes(result.error_code ?? "");
}

/** A browser checkbox only acknowledges a manual check; it never sends a POST. */
export function canPrepareAfterReview(
  reconciliationRequired: boolean,
  checkedPanelNoDraft: boolean,
): boolean {
  return !reconciliationRequired || checkedPanelNoDraft;
}

export function presentSoclickHandoff(result: SoclickHandoffResult): SoclickNotice {
  if (result.ok) {
    return {
      type: "success",
      message: result.is_existing
        ? "O rascunho já estava salvo na SóClick."
        : "Rascunho salvo na SóClick. Ainda não foi enviado para impressão.",
      nextStep: result.browser_opened === false
        ? "O navegador não abriu. Use o link para conferir o rascunho."
        : "Confira as fotos, quantidades e medidas antes de prosseguir.",
      panelUrl: result.browser_opened === false ? result.panel_url : undefined,
    };
  }
  const code = result.error_code ?? "HANDOFF_FAILED";
  switch (code) {
    case "ROOTS_NOT_CONFIGURED":
      return {
        type: "error",
        code,
        message: "O arquivo está salvo. Falta concluir a configuração inicial da SóClick.",
        nextStep: "Peça ao gestor para ativar a área segura de preparação no EvydFlow. Não precisa liberar todas as pastas do computador.",
      };
    case "HANDOFF_STAGING_FAILED":
      return {
        type: "error",
        code,
        message: "O arquivo foi salvo, mas não foi possível preparar a cópia para a SóClick.",
        nextStep: "Confira se a pasta de preparação está acessível. A foto original continua salva.",
      };
    case "OPERATOR_NOT_AUTHORIZED":
      return {
        type: "error",
        code,
        message: "O arquivo foi salvo, mas este computador não tem acesso à SóClick.",
        nextStep: "Peça ao gestor para conferir a autorização do EvydFlow.",
      };
    case "PANEL_OFFLINE":
      return {
        type: "error",
        code,
        message: "O arquivo foi salvo. O painel SóClick não está disponível neste momento.",
        nextStep: "Use Reativar painel SóClick abaixo. Se não funcionar, peça ao gestor para verificar o serviço.",
      };
    case "HANDOFF_UNCERTAIN":
      return {
        type: "error",
        code,
        message: "O arquivo foi salvo, mas não sabemos se o rascunho chegou à SóClick.",
        nextStep: "Abra o painel SóClick e procure o rascunho antes de tentar novamente. Não faça envio físico duplicado.",
      };
    case "RENDER_CHANGED":
      return {
        type: "error",
        code,
        message: "As fotos ou o arquivo mudaram após a geração.",
        nextStep: "Gere o arquivo novamente para enviar exatamente as fotos que aparecem na tela.",
      };
    case "HANDOFF_REJECTED":
      return {
        type: "error",
        code,
        message: "O arquivo foi salvo, mas a SóClick não aceitou o rascunho.",
        nextStep: "Peça ao gestor para conferir os dados do pedido e a configuração do painel.",
      };
    default:
      return {
        type: "error",
        code,
        message: "O arquivo foi salvo, mas não foi possível confirmar o rascunho na SóClick.",
        nextStep: "Confira o painel antes de tentar novamente. O arquivo continua disponível em Abrir pasta.",
      };
  }
}
