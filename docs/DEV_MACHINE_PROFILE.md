# Development / Benchmark Machine

Perfil de referência informado em 2026-10-03. Não registrar hostname, device ID ou product ID.

## Hardware

- CPU: Intel Core i7-11800H, 11ª geração
- RAM: 32 GB
- GPU: NVIDIA GeForce RTX 3060 Laptop GPU, 6 GB
- iGPU: Intel UHD Graphics
- arquitetura: x64
- armazenamento total aproximado: 1.86 TB

## Sistema

- Windows 11 Home Single Language
- versão 25H2
- build 26200.9457

## Implicações

- Este hardware é suficiente para o editor proposto.
- O renderer Pillow é predominantemente CPU/RAM; não depender de CUDA.
- WebView2/Fabric pode usar aceleração gráfica do Windows, mas nenhum requisito funcional pode depender da RTX.
- Preview de JPEGs ~8 MB deve ser rápido com proxy 2048px e cache.
- Benchmarks de release devem incluir pelo menos esta máquina, em cold e warm cache.

## Baseline de teste Windows

- x64
- Windows 11 Home 25H2
- escala de exibição real do estúdio
- caminhos com espaços e acentos
- instalação por usuário
- menu moderno do Windows 11
- fallback clássico em “Mostrar mais opções”
