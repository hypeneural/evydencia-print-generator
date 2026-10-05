import { describe, it, expect } from "vitest";
import { checkRenderEligibility, getMinimumFilledSlots } from "./render_policy";

describe("render_policy", () => {
  describe("getMinimumFilledSlots", () => {
    it("chaveiro-3x4 requires 2 slots and does not require all", () => {
      const { minimumRequired, requireAll } = getMinimumFilledSlots("chaveiro-3x4", 18);
      expect(minimumRequired).toBe(2);
      expect(requireAll).toBe(false);
    });

    it("globo-neve requires 2 slots and requires all", () => {
      const { minimumRequired, requireAll } = getMinimumFilledSlots("globo-neve", 2);
      expect(minimumRequired).toBe(2);
      expect(requireAll).toBe(true);
    });

    it("calendario-2027 requires 1 slot and requires all", () => {
      const { minimumRequired, requireAll } = getMinimumFilledSlots("calendario-2027", 1);
      expect(minimumRequired).toBe(1);
      expect(requireAll).toBe(true);
    });

    it("polaroid-natal requires 1 slot and requires all", () => {
      const { minimumRequired, requireAll } = getMinimumFilledSlots("polaroid-natal", 1);
      expect(minimumRequired).toBe(1);
      expect(requireAll).toBe(true);
    });
  });

  describe("checkRenderEligibility", () => {
    const chaveiroSlots = Array.from({ length: 18 }, (_, i) => `slot_${String(i + 1).padStart(2, "0")}`);

    it("blocks Chaveiro with 0 filled slots", () => {
      const res = checkRenderEligibility("chaveiro-3x4", chaveiroSlots, []);
      expect(res.canRender).toBe(false);
      expect(res.filledCount).toBe(0);
      expect(res.missingForRequirement).toBe(2);
      expect(res.statusMessage).toBe("Adicione pelo menos 2 fotos");
    });

    it("blocks Chaveiro with 1 filled slot", () => {
      const res = checkRenderEligibility("chaveiro-3x4", chaveiroSlots, ["slot_01"]);
      expect(res.canRender).toBe(false);
      expect(res.filledCount).toBe(1);
      expect(res.missingForRequirement).toBe(1);
      expect(res.statusMessage).toBe("Adicione mais 1 foto para gerar");
    });

    it("allows Chaveiro with exactly 2 filled slots", () => {
      const res = checkRenderEligibility("chaveiro-3x4", chaveiroSlots, ["slot_05", "slot_10"]);
      expect(res.canRender).toBe(true);
      expect(res.filledCount).toBe(2);
      expect(res.missingForRequirement).toBe(0);
      expect(res.statusMessage).toBe("Pronto para gerar");
    });

    it("allows Chaveiro with all 18 filled slots", () => {
      const res = checkRenderEligibility("chaveiro-3x4", chaveiroSlots, chaveiroSlots);
      expect(res.canRender).toBe(true);
      expect(res.filledCount).toBe(18);
      expect(res.missingForRequirement).toBe(0);
    });

    it("blocks Globo with 1 filled slot and allows with 2", () => {
      const globoSlots = ["foto_1", "foto_2"];
      const res1 = checkRenderEligibility("globo-neve", globoSlots, ["foto_1"]);
      expect(res1.canRender).toBe(false);
      expect(res1.missingForRequirement).toBe(1);

      const res2 = checkRenderEligibility("globo-neve", globoSlots, ["foto_1", "foto_2"]);
      expect(res2.canRender).toBe(true);
    });

    it("blocks Calendario with 0 filled slots and allows with 1", () => {
      const calSlots = ["foto_principal"];
      const res0 = checkRenderEligibility("calendario-2027", calSlots, []);
      expect(res0.canRender).toBe(false);
      expect(res0.statusMessage).toBe("Adicione uma foto");

      const res1 = checkRenderEligibility("calendario-2027", calSlots, ["foto_principal"]);
      expect(res1.canRender).toBe(true);
    });

    it("blocks Polaroid with 0 filled slots and allows with 1", () => {
      const polSlots = ["foto_principal"];
      const res0 = checkRenderEligibility("polaroid-natal", polSlots, []);
      expect(res0.canRender).toBe(false);

      const res1 = checkRenderEligibility("polaroid-natal", polSlots, ["foto_principal"]);
      expect(res1.canRender).toBe(true);
    });
  });
});
