![giph5lens typing](https://readme-typing-svg.demolab.com?font=Space+Mono&size=24&pause=3000&color=4AF0C8&center=true&vCenter=true&width=700&lines=giph5lens+🔮;Quando+o+Código+Vira+Lembrança;Microtube+Print+Spooler)

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-2.0-009688?style=for-the-badge&logo=fastapi&logoColor=white) ![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=for-the-badge&logo=docker&logoColor=white) ![A4](https://img.shields.io/badge/A4-300_DPI-ff5c7a?style=for-the-badge) ![feito_com](https://img.shields.io/badge/feito_com-♥_para_Dublin-7b5cfa?style=for-the-badge) ![Stack](https://img.shields.io/badge/Sistemas_Web-SC-4af0c8?style=for-the-badge)

# Quando o Código Vira Lembrança

> _Como um presente de Dia dos Namorados virou um Print Spooler, dois repositórios e um laboratório de óptica em miniatura._

---

## 👋 Contexto

Sou estudante de Sistemas Web no último semestre da faculdade em Santa Catarina.
Nas horas vagas: entusiasta de cultura maker, eletrônica, impressão 3D e de qualquer projeto que consiga transformar uma ideia em algo físico que você pode segurar na mão.

Esse projeto não nasceu de uma disciplina, de um hackathon ou de uma demanda de trabalho.

Nasceu de um problema muito pessoal.

Minha noiva mora em Dublin. O Valentine's Day estava chegando. Eu queria mandar um presente que fosse mais do que uma caixinha comprada online — queria mandar algo que eu tivesse construído, do zero, com as ferramentas que tenho.

A ideia era resgatar o espírito dos antigos monóculos fotográficos — aqueles pequenos cilindros de plástico dos anos 70 e 90 onde você apontava para a luz e via uma fotografia ampliada por uma lente — mas adicionar movimento. Uma animação óptica sutil, o tipo de coisa que parece um pouco com magia quando você gira o tubo entre os dedos.

O resultado foi um projeto que ficou maior do que o planejado, teve a rota recalculada no meio do caminho e acabou se dividindo em dois repositórios com missões completamente diferentes.

Este aqui é o giph5lens.

---

## 📸 O que é um monóculo fotográfico?

Se você já abriu uma caixa de fotos antigas dos seus pais ou avós, provavelmente encontrou um.

<p align="center">
  <i>Um pequeno cilindro. Uma lente numa ponta. Uma fotografia minúscula na outra. Você apontava para a luz e a memória aparecia ampliada na frente dos seus olhos.</i>
</p>

O monóculo fotográfico foi popular entre as décadas de 70 e 90 e representava uma época em que as memórias eram físicas. Não existia nuvem, galeria infinita no celular ou backup automático. Existia uma fotografia revelada, guardada com cuidado.

O giph5lens começou como uma tentativa de resgatar exatamente esse sentimento, usando as ferramentas que temos hoje.

---

## 💡 A ideia original

A versão inicial do projeto era ambiciosa: criar um microtubo fotográfico de 5×5 cm com **efeito lenticular** — aquela técnica em que diferentes imagens aparecem dependendo do ângulo de visão, criando uma animação sutil quando você gira o objeto.

Para funcionar, a foto precisava ser **entrelaçada matematicamente** para casar com as micro-lentes da folha lenticular (100 LPI). Um algoritmo de fatiamento vertical distribuiria pixels de 4 frames diferentes em tiras de aproximadamente 1,5 px cada, com precisão sub-pixel estilo Bresenham.

Era a parte técnica mais interessante. E também a que precisou ser pausada.

---

## 🛑 A vida real bateu na porta

Entre provas do último semestre, estágio, o prazo da entrega internacional e o preço do papel lenticular (caro, raro e cada teste físico custando dinheiro), precisei fazer o que todo desenvolvedor faz quando os requisitos mudam:

**Recalcular a rota.**

```
Problema: papel lenticular é caro, raro e exige calibração técnica por foto
Prazo:    Valentine's Day · entrega em Dublin · junho · imóvel
Decisão:  dividir o projeto em dois repositórios com missões distintas
```

---

## 🔀 Como o projeto se dividiu

```mermaid
graph TD
    ORIGEM(["💡 Presente para Dublin\nMonóculo com efeito lenticular"])

    ORIGEM --> G5["giph5lens\n📦 Print Spooler"]
    ORIGEM --> KL["KineLab\n🔬 Laboratório Óptico"]

    G5 --> G5A["Folha A4 com máximo\nde cópias 5×5 cm"]
    G5 --> G5B["300 DPI reais\nTIFF pronto para gráfica"]
    G5 --> G5C["FastAPI + Docker\npronto agora"]

    KL --> KL1["ESP32 + TFT 320×240\nPlatform.io"]
    KL --> KL2["Scanimation · Moiré\nCinemagramas · Kinegramas"]
    KL --> KL3["Entrelaçamento lenticular\n100 LPI · sub-pixel Bresenham"]
    KL --> KL4["Simulação digital de lentes\nSPIFFS · animação em display"]

    style ORIGEM fill:#0d1120,color:#4af0c8,stroke:#4af0c8
    style G5 fill:#0a1428,color:#4af0c8,stroke:#4af0c8
    style KL fill:#0d1120,color:#7b5cfa,stroke:#7b5cfa
```

| | giph5lens | KineLab |
|---|---|---|
| **Missão** | Entregar o presente agora | Explorar sem pressão de prazo |
| **Foco** | Impressão fotográfica precisa | Óptica · ESP32 · animação |
| **Status** | ✅ produção | 🔬 laboratório |
| **Stack** | Python · FastAPI · Pillow · Docker | C++ · Platform.io · TFT · SPIFFS |

---

## 🎯 O que o giph5lens faz hoje

> **Uma foto entra. Uma folha A4 sai — com o máximo de cópias 5×5 cm, 300 DPI reais, guias de corte e pronta para qualquer gráfica de bairro.**

O problema que ele resolve parece pequeno mas é mais crítico do que parece: quando você trabalha com elementos ópticos e microtubos, um redimensionamento automático de apenas 2 mm por parte do driver da impressora já compromete o resultado. O giph5lens funciona como um **Print Spooler especializado** — embute os metadados de DPI no TIFF de saída e orienta o usuário para imprimir em tamanho real, sem escalonamento.

---

## ✨ Novidades (atualização)

- Suporte a múltiplas imagens no upload (frontend aceita `multiple`).
- Opção `Repetir para preencher A4`: se ativada (`repeat`), as imagens selecionadas são ciclicamente repetidas até preencher a folha A4; se desativada, apenas as imagens enviadas serão colocadas e as posições restantes ficarão em branco.
- Botão `Limpar` para resetar o formulário e subir novas imagens do zero.
- Botão `Imprimir/PDF`: abre uma janela com o preview e aciona `window.print()` — útil para gerar um PDF local sem gastar tinta.
- API: o endpoint `/api/process` agora aceita múltiplos arquivos (`file=@a.jpg -F file=@b.jpg`) e recebe o campo `repeat` com valores `repeat` ou `no-repeat`.

Exemplo `curl` para múltiplos arquivos:

```bash
curl -X POST http://localhost:8000/api/process \
  -F "file=@foto1.jpg" \
  -F "file=@foto2.jpg" \
  -F "dpi=300" \
  -F "gap_mm=2" \
  -F "margin_mm=8" \
  -F "repeat=repeat"
```

## 🧮 A matemática do grid

```
A4 = 210 × 297 mm

foto     = 50 × 50 mm   (microtubo padrão)
gap      = 3 mm          (linha de corte)
margem   = 8 mm          (sangria da gráfica)

usable_w = 210 - 2×8 = 194 mm
usable_h = 297 - 2×8 = 281 mm

cols = ⌊(194 + 3) / (50 + 3)⌋ = ⌊197 / 53⌋ = 3
rows = ⌊(281 + 3) / (50 + 3)⌋ = ⌊284 / 53⌋ = 5

total = 3 × 5 = 15 cópias por folha A4
```

---

## 🔄 Pipeline

```mermaid
flowchart TD
    A([📷 Sua foto]) -->|POST /api/process| B[giph5lens API]

    subgraph Engine["⚙️ A4 Layout Engine"]
        B --> C[Crop quadrado central\nevita distorção em retratos]
        C --> D[Resize para photo_px²\nLANZCOS]
        D --> E[Calcula grid\ncols · rows · offsets centralizados]
        E --> F[Monta canvas A4 branco\n2480×3508 px @ 300 DPI]
        F --> G[Cola N cópias no grid]
        G --> H[Cruzetas de corte\ncinza · 1px · some na impressão]
        H --> I[Salva TIFF\nDPI metadata embutido · LZW]
        I --> J[Salva preview JPEG\n800px para o browser]
    end

    J --> K([🖥️ Preview da folha na UI])
    I --> L([⬇️ TIFF pronto para a gráfica])

    style A fill:#0d1120,color:#4af0c8,stroke:#4af0c8
    style K fill:#0d1120,color:#7b5cfa,stroke:#7b5cfa
    style L fill:#0d1120,color:#4af0c8,stroke:#4af0c8
    style Engine fill:#080e1c,color:#c8d8f0,stroke:#1a2540
```

---

## 🌐 Arquitetura

```mermaid
graph LR
    subgraph UI["🖥️ Browser"]
        F["Upload · Params · Badge dinâmico · Preview A4"]
    end

    subgraph Docker["🐳 Container giph5lens"]
        GW["FastAPI / Uvicorn\nPOST /api/process\nGET /api/layout-calc\nGET /api/status/:id\nGET /api/download/:id\nGET /api/preview/:id"]
        BG["Background Task\nasyncio"]
        ENG["A4LayoutEngine\na4_layout.py"]
        JOBS[("Job Store\nin-memory")]
    end

    subgraph FS["/tmp/microtube"]
        UP["uploads/"]
        OUT["outputs/\n.tiff + _preview.jpg"]
    end

    UI -->|HTTP| GW
    GW --> BG & JOBS
    BG --> ENG --> UP & OUT
    UI -->|polling| JOBS
    UI -->|download| OUT

    style UI fill:#060810,stroke:#1a2540,color:#c8d8f0
    style Docker fill:#0a1428,stroke:#4af0c8,color:#c8d8f0
    style FS fill:#080e1c,stroke:#7b5cfa,color:#c8d8f0
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/SEU_USUARIO/giph5lens.git
cd giph5lens

docker compose up --build
# → abra http://localhost:8000
```

**Sem Docker:**

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**CLI direta:**

```bash
# Calcular quantas fotos cabem (sem processar nada)
curl "http://localhost:8000/api/layout-calc?dpi=300&photo_mm=50&gap_mm=3&margin_mm=8"
# → {"cols":3,"rows":5,"total_photos":15,"dpi":300,...}

# Processar uma foto
curl -X POST http://localhost:8000/api/process \
  -F "file=@minha_foto.jpg" \
  -F "dpi=300" \
  -F "photo_mm=50" \
  -F "gap_mm=3" \
  -F "draw_guides=true"
# → {"job_id":"a3f2c1b0","status":"queued",...}

# Baixar o TIFF
curl http://localhost:8000/api/download/a3f2c1b0 --output giph5lens_a4.tiff
```

**CLI standalone (sem servidor):**

```bash
python -m processing.a4_layout foto.jpg saida.tiff 300 50
# → {"cols":3,"rows":5,"total_photos":15,...}
```

---

## ⚙️ Parâmetros

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `dpi` | `300` | Resolução de impressão |
| `photo_mm` | `50.0` | Tamanho da foto em mm (5 cm = microtubo padrão) |
| `gap_mm` | `3.0` | Espaço entre fotos — linha de corte |
| `margin_mm` | `8.0` | Margem externa da folha — sangria da gráfica |
| `draw_guides` | `true` | Cruzetas de corte nos cantos de cada foto |

---

## 🖨️ Do TIFF ao microtubo

```mermaid
journey
    title Do arquivo ao presente em Dublin
    section giph5lens
      Upload da foto: 5: Você
      Configurar parâmetros: 4: Você
      Baixar TIFF A4: 5: API
    section Gráfica de bairro
      Enviar o TIFF: 5: Você
      Imprimir A4 · tamanho real · sem escalar: 5: Gráfica
      Papel fotográfico 200g+: 4: Gráfica
    section Montagem do microtubo
      Cortar nas cruzetas: 3: Você
      Enrolar no cilindro: 3: Você
    section Dublin
      Entregar o presente: 5: Você
```

---

## 🧪 Testes

```bash
pytest tests/test_a4_layout.py -v
# 11 passed ✅
```

| Teste | O que garante |
|-------|--------------|
| `test_a4_300dpi_dimensions` | Canvas tem exatamente 2480×3508 px |
| `test_grid_5cm_fits` | ≥ 15 cópias numa folha A4 padrão |
| `test_dpi_metadata_embedded` | TIFF sai com DPI=300 no metadado |
| `test_preview_created_and_small` | Preview JPEG ≤ 800 px |
| `test_portrait_source_crops_to_square` | Foto retrato não distorce |
| `test_background_is_white` | Fundo da folha é branco puro |

---

## 🗂️ Estrutura do projeto

```
giph5lens/
│
├── 🐳 Dockerfile
├── 🐳 docker-compose.yml
├── 📦 requirements.txt
│
├── app/
│   ├── main.py               ← FastAPI v2: A4 layout · job queue · endpoints
│   └── templates/
│       └── index.html        ← UI com badge dinâmico e preview da folha A4
│
├── processing/
│   ├── a4_layout.py          ← ⭐ motor principal: grid engine · crop · guias de corte
│   └── interlace.py          ← pausado → exploração continua no KineLab
│
└── tests/
    ├── test_a4_layout.py     ← 11 testes · 0 falhas
    └── test_interlace.py     ← mantido como referência histórica
```

---

## 🔬 E o KineLab?

Enquanto o giph5lens resolve o problema imediato da impressão, o **KineLab** é o espaço onde a pesquisa continua sem prazo e sem pressão.

É lá que estou explorando:

- **ESP32 + displays TFT** via Platform.io
- **Scanimation** — sequências de quadros reveladas por uma máscara móvel
- **Efeito Moiré** — padrões visuais gerados pela sobreposição de grades
- **Grades de barreira** — animações baseadas em ângulo de visão
- **Cinemagramas e Kinegramas** — animação produzida pelo movimento físico de uma nota sobre uma imagem intercalada
- **Simulação digital de lentes lenticulares** — preview sem papel lenticular físico
- **Entrelaçamento sub-pixel** — o algoritmo Bresenham que ficou de fora desta versão

> O presente para Dublin foi apenas o ponto de partida. O laboratório continua aberto.

---

## 🗺️ Roadmap

```mermaid
gantt
    dateFormat  YYYY-MM
    title giph5lens — o caminho até aqui e o que vem depois
    section v1 · Conceito
        Ideia do microtubo lenticular   :done,    2025-05, 1M
        Algoritmo de entrelaçamento     :done,    2025-05, 1M
    section v2 · Print Spooler
        A4 layout engine                :done,    2025-06, 1M
        UI com badge e preview A4       :done,    2025-06, 1M
        Docker · testes · justfile      :done,    2025-06, 1M
    section v2.1 · Próximos
        Export PDF com metadados        :active,  2025-07, 1M
        Suporte a múltiplas fotos       :         2025-07, 1M
    section v3 · Convergência
        Bridge KineLab → giph5lens      :         2025-10, 2M
        Entrelaçamento de volta ao repo :         2025-12, 2M
```

---

## 🤝 Contribuindo

Esse projeto foi feito por um estudante com um prazo, um ESP32 na mesa e muita vontade de aprender. Qualquer contribuição é bem-vinda — especialmente de quem trabalha com impressão, óptica ou eletrônica maker.

```bash
git checkout -b feat/minha-contribuicao
# faça as mudanças
pytest tests/ -v     # todos devem passar
git commit -m "feat: descrição clara"
git push origin feat/minha-contribuicao
```

---

Sistemas Web · Santa Catarina · último semestre · Maker nas horas vagas · entusiasta de tudo que vira objeto físico

**giph5lens** — quando o código vira lembrança · feito com ♥ e muito Pillow para Dublin
