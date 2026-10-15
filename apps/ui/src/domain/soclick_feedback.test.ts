import { describe, expect, it } from "vitest";
import { presentSoclickHandoff } from "./soclick_feedback";

describe("SóClick handoff — operator messages remain safe and understandable", () => {
  it("keeps local JPEG success separate from missing allowed roots", () => {
    const notice = presentSoclickHandoff({
      ok: false,
      error_code: "ROOTS_NOT_CONFIGURED",
      error: "Falha na SóClick (503): Configure EVYDFLOW_ALLOWED_ROOTS",
    });
    expect(notice.type).toBe("error");
    expect(notice.message).toContain("arquivo foi salvo");
    expect(notice.nextStep).toContain("gestor");
    expect(JSON.stringify(notice)).not.toContain("EVYDFLOW_ALLOWED_ROOTS");
    expect(JSON.stringify(notice)).not.toContain("503");
  });

  it("never advises automatic retry when timeout or result is uncertain", () => {
    const notice = presentSoclickHandoff({ ok: false, error_code: "HANDOFF_UNCERTAIN" });
    expect(notice.message).toContain("não sabemos");
    expect(notice.nextStep).toContain("antes de tentar novamente");
    expect(notice.nextStep).toContain("Não faça envio físico duplicado");
  });

  it("distinguishes offline panel from loss of internet", () => {
    const notice = presentSoclickHandoff({ ok: false, error_code: "PANEL_OFFLINE" });
    expect(notice.nextStep).toContain("EvydFlow");
    expect(notice.message).toContain("O arquivo foi salvo");
  });

  it("explains authentication failure without showing the token or raw details", () => {
    const notice = presentSoclickHandoff({
      ok: false,
      error_code: "OPERATOR_NOT_AUTHORIZED",
      error: "Bearer TOP-SECRET and C:\\Private\\Users",
    });
    expect(notice.nextStep).toContain("gestor");
    expect(JSON.stringify(notice)).not.toContain("TOP-SECRET");
  });

  it("explains stale render and requests a fresh local JPEG", () => {
    const notice = presentSoclickHandoff({ ok: false, error_code: "RENDER_CHANGED" });
    expect(notice.nextStep).toContain("Gere o arquivo novamente");
  });

  it("unknown errors fail closed without exposing arbitrary backend text", () => {
    const notice = presentSoclickHandoff({
      ok: false,
      error_code: "SOME_NEW_CODE",
      error: "C:\\secret\\customer-photo.jpg",
    });
    expect(notice.type).toBe("error");
    expect(notice.nextStep).toContain("Confira o painel");
    expect(JSON.stringify(notice)).not.toContain("customer-photo");
  });

  it("success confirms draft only, never physical printing", () => {
    const notice = presentSoclickHandoff({ ok: true, browser_opened: true });
    expect(notice.message).toContain("não foi enviado para impressão");
    expect(notice.panelUrl).toBeUndefined();
  });

  it("browser launch failure preserves a link to the already-created draft", () => {
    const url = "http://127.0.0.1:8095/panel/soclick?focus=job_print_123#review";
    const notice = presentSoclickHandoff({
      ok: true,
      browser_opened: false,
      panel_url: url,
    });
    expect(notice.panelUrl).toBe(url);
    expect(notice.nextStep).toContain("navegador não abriu");
  });
});
