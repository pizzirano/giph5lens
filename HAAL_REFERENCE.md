<!-- GUIA DE REFERÊNCIA: Arquitetura HAAL Refatorada
     Keepgram v3.0 — FastAPI + HTMX + Alpine.js + Vanilla CSS
     
     Este arquivo mostra exemplos práticos de cada camada da arquitetura HAAL.
     Manter como referência para novas features.
-->

<!-- ═══════════════════════════════════════════════════════════════════════════
     EXEMPLO 1: Componente Upload com Alpine.js
     ═════════════════════════════════════════════════════════════════════════ -->

ANTES (JavaScript imperativo):
───────────────────────────────
fi.addEventListener('change', () => {
  addFiles([...fi.files]);
  fi.value = '';
});

function addFiles(newFiles) {
  newFiles.forEach(f => {
    if (files.length >= 70) return;
    if (!f.type.startsWith('image/')) return;
    files.push(f);
  });
  renderThumbs();
  checkCropRisk();
  syncRun();
  fetchBadge();
}

function renderThumbs() {
  [...thumbsEl.querySelectorAll('.thumb')].forEach(t => t.remove());
  files.forEach((f, i) => {
    const url = URL.createObjectURL(f);
    const div = document.createElement('div');
    div.className = 'thumb';
    div.innerHTML = `<img src="${url}" alt="frame ${i+1}"/>...`;
    thumbsEl.insertBefore(div, thumbAdd);
  });
}

DEPOIS (Alpine.js Declarativo):
────────────────────────────────
<input type="file" accept="image/*" multiple 
       @change="$parent.addFiles([...$event.target.files]); $event.target.value = ''" />

<template x-for="(file, index) in $parent.files" :key="index">
  <div class="thumb">
    <img :src="URL.createObjectURL(file)" :alt="'frame ' + (index + 1)" />
    <button class="thumb-rm" @click="$parent.removeFile(index)">×</button>
  </div>
</template>

Benefício: Sem DOM manipulation, tudo reativo e sincronizado automaticamente.


<!-- ═══════════════════════════════════════════════════════════════════════════
     EXEMPLO 2: Modal com Alpine.js (x-show)
     ═════════════════════════════════════════════════════════════════════════ -->

ANTES (classList manual):
────────────────────────
btnRun.addEventListener('click', () => {
  if (mode === 'a4' && files.length < 70) {
    // preencher dados do modal
    mN.textContent = files.length;
    mN2.textContent = files.length;
    // ... mais manipulações
    modalBg.classList.add('vis');
  }
});

function confirmFill(fill) {
  modalBg.classList.remove('vis');
  startJob(fill);
}

DEPOIS (Alpine.js x-show):
──────────────────────────
<div class="modal-bg" :class="{ vis: $root.showModal }">
  <div class="modal">
    <button @click="$root.confirmFill('repeat')">🔁 Repetir até 70</button>
    <button @click="$root.confirmFill('exact')">📐 Só as <span id="m-n2">?</span> fotos</button>
  </div>
</div>

<!-- Em base.html appState(): -->
<script>
confirmFill(fillMode) {
  this.showModal = false;  // Automático, sem classList!
  this.submitJob(fillMode);
}
</script>

Benefício: Estado booleano, sem DOM queries.


<!-- ═══════════════════════════════════════════════════════════════════════════
     EXEMPLO 3: Polling com HTMX (vs setInterval)
     ═════════════════════════════════════════════════════════════════════════ -->

ANTES (setInterval manual):
───────────────────────────
timer = setInterval(poll, 900);

async function poll() {
  try {
    const d = await fetch('/api/status/' + jobId).then(r => r.json());
    if (d.status === 'processing') {
      pb.style.width = '65%';
      setSm(d.message, '');
    }
    if (d.status === 'done') {
      clearInterval(timer);  // ← Limpar manualmente
      pb.style.width = '100%';
      setSm(d.message, 'ok');
      markDone(3); markDone(4);
      showResult(d.info);
    }
  } catch {}
}

DEPOIS (HTMX + Alpine):
──────────────────────
// Em base.html submitJob():
htmx.ajax('GET', '/api/status-html/' + data.job_id, {
  target: statusDiv,
  swap: 'innerHTML',
  trigger: 'load, every 1s'  // ← Declarativo!
});

<!-- Em templates/components/process-step.html -->
<div id="polling-status"></div>

<!-- HTMX para automaticamente: -->
<!-- 1. Requisição GET cada 1s -->
<!-- 2. Injetar HTML retornado -->
<!-- 3. Parar quando job.status === "done" -->

// Em main.py /api/status-html/{job_id}:
if job.status == "done":
  return HTMLResponse(html)  # Sem hx-trigger, polling para

Benefício: Sem setInterval, sem clearInterval, sem erro de timing.


<!-- ═══════════════════════════════════════════════════════════════════════════
     EXEMPLO 4: Upload com FormData (HTMX × Fetch Manual)
     ═════════════════════════════════════════════════════════════════════════ -->

ANTES (Fetch + FormData manual):
────────────────────────────────
const fd = new FormData();
files.forEach(f => fd.append('files', f));
fd.append('mode', mode);
fd.append('dpi', document.getElementById('p-dpi').value);
// ... 10 mais linhas

const r = await fetch('/api/process', { method: 'POST', body: fd });
const d = await r.json();
if (!r.ok) throw new Error(d.detail || 'Erro');

DEPOIS (Alpine + Fetch simplificado):
──────────────────────────────────────
async submitJob(fillMode) {
  const fd = new FormData();
  this.files.forEach(f => fd.append('files', f));
  fd.append('mode', this.mode);
  fd.append('dpi', this.dpi);
  // ... valores vêm de this.* (estado Alpine)
  
  const resp = await fetch('/api/process', { method: 'POST', body: fd });
  const data = await resp.json();
  this.jobId = data.job_id;
  
  // Inicia polling HTMX
  htmx.ajax('GET', '/api/status-html/' + data.job_id, {...});
}

Benefício: FormData construído a partir do estado Alpine (simples, sem DOM queries).


<!-- ═══════════════════════════════════════════════════════════════════════════
     EXEMPLO 5: Estrutura de Diretórios (Antes × Depois)
     ═════════════════════════════════════════════════════════════════════════ -->

ANTES (Monolítico):
──────────────────
app/
├── main.py
└── templates/
    └── index.html  ← 505 linhas (CSS inline + JS inline)

DEPOIS (Modular - HAAL):
───────────────────────
app/
├── main.py                    ← Ajustado (app.mount("/static", ...))
├── templates/
│   ├── base.html             ← 225 linhas (Alpine.js + includes)
│   ├── components/           ← 4 fragmentos independentes
│   │   ├── upload-step.html  ← ~50 linhas
│   │   ├── params-step.html  ← ~60 linhas
│   │   ├── process-step.html ← ~30 linhas
│   │   └── result-step.html  ← ~40 linhas
│   └── modals/
│       └── fill-mode-modal.html ← ~25 linhas
└── static/
    └── css/
        └── style.css          ← 766 linhas (antes inline)

Benefício:
- Cada arquivo tem responsabilidade única
- Fácil de encontrar o que precisa editar
- Reutilizável em múltiplas páginas


<!-- ═══════════════════════════════════════════════════════════════════════════
     GUIA RÁPIDO: Quando Usar Cada Tecnologia
     ═════════════════════════════════════════════════════════════════════════ -->

┌─ Alpine.js (Estado Local)
│  ├─ Abrir/fechar modal → ✓ showModal = true/false
│  ├─ Renderizar thumbnails → ✓ x-for="file in files"
│  ├─ Validar formulário → ✓ x-show="dpi < 150"
│  ├─ Upload para servidor → ✗ Use HTMX
│  └─ Polling → ✗ Use HTMX
│
├─ HTMX (Comunicação Assíncrona)
│  ├─ Upload de arquivos → ✓ hx-post="/api/process"
│  ├─ Polling → ✓ hx-trigger="every 1s"
│  ├─ Injetar resultado → ✓ hx-swap="innerHTML"
│  ├─ Cálculo local → ✗ Use Alpine
│  └─ Mostrar/esconder elemento → ✗ Use Alpine x-show
│
├─ FastAPI (Backend)
│  ├─ Processar arquivos → ✓ @app.post("/api/process")
│  ├─ Retornar JSON → ✓ return {...}
│  ├─ Retornar HTML → ✓ return HTMLResponse(html)
│  ├─ Servir página completa → ✓ return templates.TemplateResponse(...)
│  └─ Servir CSS → ✓ app.mount("/static", StaticFiles(...))
│
└─ CSS (Estilos)
   ├─ Cores, fonts, layout → ✓ static/css/style.css
   ├─ Variáveis CSS → ✓ :root { --accent: #4af0c8; }
   ├─ Responsividade → ✓ @media (max-width: 768px)
   ├─ Classes Tailwind → ✗ Use Vanilla CSS
   └─ Lógica de UI → ✗ Use Alpine


<!-- ═══════════════════════════════════════════════════════════════════════════
     CHECKLIST: Adicionar Nova Feature na Stack HAAL
     ═════════════════════════════════════════════════════════════════════════ -->

Exemplo: Adicionar campo "Qualidade de Compressão"

1. BACKEND (main.py)
   [ ] Adicionar parâmetro em @app.post("/api/process")
   [ ] Passar para MonocleConfig
   [ ] Testar com pytest

2. FRONTEND - Alpine State (base.html)
   [ ] Adicionar propriedade em appState()
   [ ] Adicionar método se necessário
   [ ] Inicializar com valor padrão

3. FRONTEND - HTML (components/params-step.html)
   [ ] Criar <input> ou <select>
   [ ] Vincular com x-model="$parent.compression"
   [ ] Adicionar label e hint

4. FRONTEND - CSS (static/css/style.css)
   [ ] Usar classe .pf existente
   [ ] Se precisa novo estilo, adicionar com variáveis CSS
   [ ] Testar responsividade

5. TESTES
   [ ] pytest tests/ -v
   [ ] Testar no navegador (Chrome DevTools)
   [ ] Validar em mobile (768px)

═════════════════════════════════════════════════════════════════════════════
FIM DO GUIA DE REFERÊNCIA
═════════════════════════════════════════════════════════════════════════════
-->
