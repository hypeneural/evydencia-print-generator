---
name: windows-shell-integration
description: "Projeta, implementa e audita integração profissional com Windows 11 Explorer: IExplorerCommand, sparse MSIX, signing, fallback clássico, CLI, pywebview e installer. Use em menu de contexto, host desktop e distribuição."
---
# Windows Shell Integration

Leia primeiro:
- `docs/WINDOWS_CONTEXT_MENU_PRO.md`
- `docs/DEV_MACHINE_PROFILE.md`
- `native/windows-shell/AGENTS.md`

Use resources desta skill apenas quando necessário.

## Decision tree

### Precisa aparecer no menu moderno do Windows 11?
Sim → `IExplorerCommand` + package identity/sparse MSIX.

### É build local/CI sem assinatura?
Use classic fallback/CLI para testes funcionais. Não alegue cobertura do tier-1 moderno.

### O handler precisa processar a foto?
Não. Pare. Extraia paths e lance o app.

### Seleção múltipla pode estourar command line?
Use shell-request manifest temporário; não copie pixels.

## Produção

```text
Explorer
  -> EvydenciaShellExtension.dll (C++)
  -> IExplorerCommand::Invoke
  -> EvydenciaPrintGenerator.exe
  -> IngestService
```

## GetState
- filtros baratos por seleção/extensão;
- supported image → enabled;
- seleção incompatível → hidden/disabled;
- sem open/decode/stat pesado.

## Signing
Sparse MSIX moderno exige assinatura/trust. Chave privada nunca entra no Git.

## Test matrix
Ver `resources/windows11-test-matrix.md`.

## Referências
Ver:
- `resources/microsoft-modern-menu.md`
- `resources/powertoys-patterns.md`

## Definition of Done
- modern menu real validado no Windows 11 Home 25H2;
- fallback clássico funcional;
- install/update/uninstall sem resíduos;
- Unicode/space/long path;
- Explorer permanece responsivo;
- CI separa testes signed e unsigned.
