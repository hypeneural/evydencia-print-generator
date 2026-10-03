# Windows 11 Professional Context Menu Architecture

## Decisão

Para produção em Windows 11, o alvo é o **menu moderno** do Explorer:

```text
File Explorer
    │
    ▼
IExplorerCommand
native x64 COM DLL
    │
    ▼
signed sparse MSIX identity
    │
    ▼
EvydenciaPrintGenerator.exe
```

O menu clássico continua como fallback, desenvolvimento e recuperação.

## Por que

A documentação oficial da Microsoft exige `IExplorerCommand` + identidade de pacote para aparecer no menu moderno do Windows 11. Um app Win32 unpackaged pode obter identidade por **sparse package**.

Referência oficial:
https://learn.microsoft.com/windows/apps/desktop/modernize/integrate-packaged-app-with-file-explorer

## Compatibilidade com Windows 11 Home

Não há requisito de edição Pro/Enterprise nessa API. O alvo real do projeto é:
- Windows 11 Home 25H2
- x64
- build de referência 26200.9457

A DLL precisa ser x64 para corresponder ao Explorer x64.

## Componentes

### 1. `EvydenciaShellExtension.dll`
C++ nativo, mínimo, sem Python/Fabric/Pillow.

Implementa:
- `IExplorerCommand::GetTitle`
- `GetIcon`
- `GetState`
- `Invoke`
- `GetCanonicalName`
- `GetFlags`
- opcionalmente `EnumSubCommands` depois

### 2. Sparse MSIX
Responsável por:
- package identity;
- registro `windows.comServer`;
- registro `windows.fileExplorerContextMenus`;
- referência à DLL externa/instalada;
- signing.

### 3. Main app
`EvydenciaPrintGenerator.exe` recebe seleção e abre o editor.

### 4. Classic fallback
Registro per-user/classic verb, visível em **Mostrar mais opções**, usado:
- em builds locais sem assinatura;
- se o modern package não registrar;
- como caminho de recuperação.

## Regra crítica de performance

Microsoft documenta que métodos de criação do menu rodam no caminho de UI do Explorer. Portanto:

### `GetTitle/GetIcon/GetState`
Podem:
- ler seleção;
- olhar extensão/nome;
- decidir visible/enabled.

Não podem:
- abrir Pillow;
- decodificar imagem;
- ler EXIF/ICC;
- chamar Python;
- acessar rede;
- inicializar WebView;
- fazer hash de arquivo;
- esperar processo.

### `Invoke`
Deve:
1. enumerar `IShellItemArray`;
2. obter paths suportados;
3. disparar processo externo;
4. retornar rapidamente.

Toda preparação de preview ocorre no app, nunca no shell extension.

## ItemType

Registrar `desktop5:ItemType Type="*"` e filtrar em `GetState`:
- .jpg
- .jpeg
- .png
- formatos adicionais somente depois de ingest/testes.

Seleção sem imagem suportada retorna `ECS_HIDDEN`.

## Single e multi-select

### Primeiro release
- 1 arquivo obrigatório;
- suporte a N arquivos somente se os testes de shell/CLI estiverem prontos.

### Caminho profissional para N arquivos
Evitar depender indefinidamente de uma linha de comando gigantesca. Se a seleção serializada ultrapassar limite seguro:
1. shell cria request manifest pequeno em diretório temp por usuário;
2. inicia app com `--shell-request <path>`;
3. app lê e remove/expira request.

Nenhuma foto é copiada para esse manifest; apenas paths.

## UX do menu

V1 moderna:
**Gerar com EVYDÊNCIA**

Abre o app já com as fotos selecionadas.

Depois de estabilizar o CLI pode-se considerar `EnumSubCommands`:
- Calendário
- Chaveiro
- Globo
- Abrir editor

Não criar submenu antes de haver contratos de seleção claros por produto.

## Signing

### Desenvolvimento
- certificado de desenvolvimento/self-signed confiado localmente;
- nunca commitar chave privada/certificado de assinatura.

### Release
- pacote moderno precisa ser assinado;
- publisher do package deve corresponder ao certificado;
- installer e package usam pipeline reproduzível.

CI sem assinatura não deve alegar que testou o menu moderno real.

## Instalação

Preferência: **per-user**.
- app em `%LOCALAPPDATA%\EVYDENCIA\PrintGenerator`;
- registro clássico em HKCU/HKA por usuário;
- sparse package registrado para o usuário;
- sem admin, salvo requisito demonstrado.

PowerToys também usa instalação per-user e sparse MSIX para handlers modernos.

## Testes obrigatórios

### Shell contract
- command visible em JPG/JPEG/PNG;
- hidden em TXT/EXE;
- 1 seleção;
- multi-select suportado quando implementado;
- Unicode;
- espaço;
- long path;
- arquivo removido entre menu e Invoke;
- app já aberto;
- app fechado.

### Installer lifecycle
- install;
- menu aparece;
- update;
- package antigo removido/atualizado;
- uninstall;
- menu some;
- nenhum CLSID/package órfão;
- restart Explorer/sign-out somente quando realmente necessário.

### Performance
- abrir menu não pode introduzir jank perceptível;
- `GetState` deve ser trivial;
- qualquer operação lenta sai do shell.

## Referências de implementação

1. Microsoft packaged desktop context menu docs.
2. Microsoft `ExplorerCommandVerb` sample.
3. PowerToys context-menu docs.
4. PowerRename/ImageResizer para dual registration, sparse MSIX e launch externo.

Não copiar PowerToys inteiro; extrair padrões de registration, GetState, Invoke, signing e lifecycle.
