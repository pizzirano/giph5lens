<p align="center">
  <br/>
  <img src="https://readme-typing-svg.demolab.com?font=Space+Mono&size=28&pause=2000&color=4AF0C8&center=true&vCenter=true&width=700&lines=giph5lens+🔮;A+Polaroid+que+se+move.;Memória+viva+em+5+cm." alt="typing" />
  <br/><br/>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-microservice-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/LPI-100-7b5cfa?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/feito_com-♥-ff5c7a?style=for-the-badge"/>
  <br/><br/>
</p>

> **giph5lens** é um Print Server especializado para microtubo lenticular.  
> Você envia frames. A API entrega um arquivo TIFF pronto para impressão — matematicamente perfeito para as lentes de 100 LPI.  
> Nada de Photoshop, nada de cálculo manual. Só o movimento.

---

## 💡 A Diferença

A Polaroid captura um instante e entrega papel.  
A **giph5lens** captura um instante e entrega **movimento**.

| Atributo | Polaroid Tradicional | giph5lens Printer |
|---|---|---|
| Formato | Plano e estático | Cilíndrico · Microtubo 5×5 cm |
| Efeito | Foto que aparece | "Holograma" sutil e romântico |
| Tecnologia | Química de revelação | Entrelaçamento digital sub-pixel |
| Interação | Ver a foto | **Girar o tubo para ver o movimento** |
| Complexidade | Zero | Zero — a API resolve tudo |

> Nasceu como presente de Dia dos Namorados.  
> Cresceu e virou um microserviço de impressão especializado.

---

## 🧮 O Motor: Matemática do Entrelaçamento

Toda a "mágica" parte de duas constantes físicas da folha lenticular:

```
total_px  =  round(size_cm / 2.54 × dpi)
           =  round(5 / 2.54 × 300)  →  591 px

strip_w   =  total_px / (lpi × n_frames)
           =  591 / (100 × 4)  →  1.4775 px  ← sub-pixel
```

Como `1.4775 px` não é inteiro, o algoritmo usa **distribuição de erro Bresenham**:  
cada tira alterna entre `floor` e `ceil`, garantindo que a soma exata = `591 px`.  
Desalinhar isso em 1 px a 100 LPI = animação quebrada. Por isso isso não é um script, é um servidor.

---

## 🔄 Pipeline Completo

```mermaid
flowchart TD
    A([👤 Cliente]) -->|POST /print\n2–4 frames + params| B[API giph5lens]

    subgraph Motor ["⚙️ Motor de Entrelaçamento"]
        B --> C{n_frames\n2–4?}
        C -->|❌| ERR([422 Unprocessable])
        C -->|✅| D[Normalização\nresize → 591² px\nLANZCOS · RGB]
        D --> E[Cálculo de Pitch\ntotal_px · strip_w · Bresenham]
        E --> F[Loop de Entrelaçamento\nF1→F2→F3→F4→repete\npor coluna]
        F --> G{sharpen?}
        G -->|sim| H[UnsharpMask\nradius 0.5 · 80%]
        G -->|não| I
        H --> I[Encode TIFF\nDPI metadata · LZW · 1:1]
        I --> J[Encode JPEG preview\n600px · browser]
    end

    J --> K([🖥️ Preview circular])
    I --> L([⬇️ TIFF pronto para impressão])

    style A fill:#0d1120,color:#4af0c8,stroke:#4af0c8
    style ERR fill:#0d1120,color:#ff5c7a,stroke:#ff5c7a
    style K fill:#0d1120,color:#7b5cfa,stroke:#7b5cfa
    style L fill:#0d1120,color:#4af0c8,stroke:#4af0c8
    style Motor fill:#080e1c,color:#c8d8f0,stroke:#1a2540
```

---

## 🌐 Arquitetura como Microserviço

```mermaid
graph TB
    subgraph Clientes ["Clientes (futuro)"]
        WEB["🖥️ Web UI\nindex.html"]
        KIOSK["🏪 Quiosque\nde presentes"]
        EXT["📱 App externo\nvia REST"]
    end

    subgraph Docker ["🐳 giph5lens container"]
        direction TB
        GW["⚡ FastAPI Gateway\nPOST /print\nGET /status/:id\nGET /download/:id\nGET /preview/:id"]
        BG["🔄 Background Worker\nasyncio · job queue"]
        PROC["🧠 InterlaceProcessor\nBresenham sub-pixel\nPillow · NumPy"]
        STORE[("📋 Job Store\nin-memory → Redis v2")]
    end

    subgraph FS ["💾 Volumes"]
        UP["📁 /uploads"]
        OUT["📁 /outputs\n.tiff + _preview.jpg"]
    end

    WEB & KIOSK & EXT -->|HTTP| GW
    GW --> BG
    GW <--> STORE
    BG --> PROC
    PROC --> UP & OUT

    style Clientes fill:#060810,stroke:#1a2540,color:#c8d8f0
    style Docker fill:#0a1428,stroke:#4af0c8,color:#c8d8f0
    style FS fill:#080e1c,stroke:#7b5cfa,color:#c8d8f0
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/SEU_USUARIO/giph5lens.git
cd giph5lens

docker compose up --build
# → http://localhost:8000
```

**API direta (sem UI):**

```bash
curl -X POST http://localhost:8000/api/process \
  -F "files=@foto1.jpg" \
  -F "files=@foto2.jpg" \
  -F "files=@foto3.jpg" \
  -F "files=@foto4.jpg" \
  -F "lpi=100" \
  -F "dpi=300" \
  -F "size_cm=5.0"

# → { "job_id": "a3f2c1b0", "status": "queued", ... }

curl http://localhost:8000/api/download/a3f2c1b0 --output microtubo.tiff
```

**CLI standalone:**

```bash
pip install -r requirements.txt
python -m processing.interlace f1.jpg f2.jpg f3.jpg f4.jpg saida.tiff
# ✓ total_px=591  strip=1.4775px
```

---

## ⚙️ Parâmetros da API

| Parâmetro | Padrão | Range | Descrição |
|-----------|--------|-------|-----------|
| `lpi` | `100` | 60–200 | Linhas/polegada da folha lenticular |
| `dpi` | `300` | 150–600 | Resolução de impressão |
| `size_cm` | `5.0` | 2–20 | Tamanho do microtubo em cm |
| `n_frames` | auto | 2–4 | Detectado pelo nº de arquivos enviados |

> **Sweet spot identificado:** 4 frames entrega animação fluida mesmo que  
> o ideal matemático puro para 300 DPI/100 LPI sejam 3 — a nitidez  
> é compensada via UnsharpMask no servidor.

---

## 🖨️ Da API ao Holograma

```mermaid
journey
    title giph5lens → Presente físico
    section API
      POST /api/process com os frames: 5: Você
      Polling GET /api/status/:id: 4: App
      Download do TIFF gerado: 5: App
    section Gráfica
      Abrir TIFF no software de impressão: 4: Você
      Definir 5×5 cm EXATO sem escalar: 5: Você
      Papel fotográfico brilhante 300g+: 5: Gráfica
    section Montagem
      Cortar em 5×5 cm: 3: Você
      Enrolar na folha lenticular: 3: Você
      Encapsular no tubo transparente: 3: Você
    section Entrega
      Dar de presente 💕: 5: Você
      Ver a pessoa girar o tubo: 5: Os dois
```

---

## 🗂️ Estrutura

```
giph5lens/
│
├── 🐳 Dockerfile
├── 🐳 docker-compose.yml
├── 📦 requirements.txt
│
├── app/
│   ├── main.py               ← FastAPI · rotas · job queue
│   └── templates/
│       └── index.html        ← UI dark holográfica (zero dependências)
│
├── processing/
│   └── interlace.py          ← ⭐ motor: Bresenham sub-pixel + Pillow/NumPy
│
└── tests/
    └── test_interlace.py     ← 11 testes · 0 falhas
```

---

## 🧪 Testes

```bash
pytest tests/ -v
# 11 passed in 0.27s ✅
```

| Teste | Garante |
|-------|---------|
| `test_total_px_5cm_300dpi` | 5 cm @ 300 DPI = 591 px exatos |
| `test_recalc_strip_4_frames` | strip = 1.4775 px |
| `test_output_shape` | TIFF tem dimensões corretas |
| `test_output_has_dpi_metadata` | Metadado DPI preservado para impressão 1:1 |
| `test_total_columns_match` | Soma Bresenham = total\_px sem off-by-one |
| `test_interlacing_alternates_frames` | Frames realmente se intercalam |
| `test_preview_created` | JPEG preview ≤ 600 px gerado |
| `test_rejects_single_frame` | < 2 frames → ValueError |

---

## 🗺️ Roadmap

```mermaid
gantt
    dateFormat  YYYY-MM
    title giph5lens — do presente ao produto
    section v1.0 · Base
        Print server completo         :done,    2025-06, 1M
        Docker + 11 testes            :done,    2025-06, 1M
    section v1.1 · UX
        Preview animado canvas        :active,  2025-07, 1M
        Export PDF com marcas de corte:         2025-07, 1M
    section v1.2 · IA
        Geração de frames via API IA  :         2025-08, 2M
        Variações automáticas de pose :         2025-09, 1M
    section v2.0 · Produto
        Suporte 6 e 8 frames          :         2025-10, 2M
        SDK para quiosques de presente:         2025-11, 1M
        SaaS hosted (giph5lens.io)    :         2026-01, 3M
```

**A visão de longo prazo:** um endpoint público onde qualquer app de presente envia fotos e recebe de volta um TIFF pronto — a inteligência por trás de quiosques físicos, e-commerces de presentes personalizados e máquinas vending de microtubo.

---

## 🤝 Contribuindo

PRs bem-vindos. Áreas prioritárias:

- Algoritmo para LPI não-standard (75, 150, 200)
- Suporte a parallax (frames com perspectivas levemente diferentes)
- Modo `--dry-run` que retorna só os cálculos sem processar
- Testes de ponta a ponta com impressão real

```bash
git checkout -b feat/minha-contribuicao
# faça as mudanças
pytest tests/ -v          # todos devem passar
git commit -m "feat: descrição"
git push origin feat/minha-contribuicao
```

---

<p align="center">
  <sub><b>giph5lens</b> — a Polaroid que entrega movimento</sub><br/>
  <sub>Nasceu de um presente · cresceu virou um microserviço · quer virar um produto</sub><br/><br/>
  <sub>Feito com ♥ e muito <code>numpy</code></sub>
</p>