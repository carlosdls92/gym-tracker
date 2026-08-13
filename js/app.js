const CDN = 'https://cdn.jsdelivr.net/gh/JahelCuadrado/ExerciseGymGifsDB@v1.1.0/';
let dlCancelled = false;

function cancelDownload() {
  dlCancelled = true;
  document.getElementById('dlOverlay').classList.remove('active');
}

async function blobToDataUri(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

async function downloadAllDays() {
  dlCancelled = false;
  const overlay  = document.getElementById('dlOverlay');
  const dlTitle  = document.getElementById('dlTitle');
  const dlSub    = document.getElementById('dlSub');
  const dlBar    = document.getElementById('dlBar');
  const dlStatus = document.getElementById('dlStatus');
  const btn      = document.getElementById('btn-dl-all');

  dlTitle.textContent  = 'INICIACIÓN';
  dlSub.textContent    = 'Preparando los 3 días en un único archivo…';
  dlBar.style.width    = '0%';
  dlStatus.textContent = 'Cargando páginas…';
  overlay.classList.add('active');
  btn.disabled = true;

  try {
    // 1. Fetch los 3 HTMLs en paralelo
    const htmls = await Promise.all(
      [1, 2, 3].map(d =>
        fetch('gym-dia' + d + '.html').then(r => {
          if (!r.ok) throw new Error('No se pudo cargar gym-dia' + d + '.html');
          return r.text();
        })
      )
    );
    if (dlCancelled) throw new Error('cancelled');

    // 2. Recolectar todas las URLs únicas entre los 3 días
    const cdnRe = new RegExp(CDN.replace(/\./g, '\\.').replace(/\//g, '\\/') + '[^"]+\\.gif', 'g');
    const allUrls = [...new Set(htmls.flatMap(h => h.match(cdnRe) || []))];
    const total = allUrls.length;
    dlStatus.textContent = total + ' imágenes únicas — descargando una sola vez…';

    // 3. Descargar cada GIF único una sola vez → mapa URL→base64
    const b64Map = {};
    for (let i = 0; i < allUrls.length; i++) {
      if (dlCancelled) throw new Error('cancelled');
      dlBar.style.width = Math.round((i / total) * 80) + '%';
      dlStatus.textContent = 'Imagen ' + (i + 1) + ' / ' + total + '…';
      try {
        const blob = await fetch(allUrls[i]).then(r => r.blob());
        b64Map[allUrls[i]] = await blobToDataUri(blob);
      } catch (e) { console.warn('No se pudo cargar:', allUrls[i]); }
    }

    dlBar.style.width = '83%';
    dlStatus.textContent = 'Ensamblando archivo combinado…';

    // 4. Reemplazar URLs en cada HTML con base64
    const processed = htmls.map(html => {
      let h = html;
      for (const [url, b64] of Object.entries(b64Map)) h = h.split(url).join(b64);
      return h.replace(/Imágenes:.*?CDN/, 'Imágenes: ExerciseGymGifsDB (embebidas)');
    });

    // 5. Escapar contenido para el atributo srcdoc
    const esc = s => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;');

    // 6. Generar HTML combinado: tab bar + 3 iframes srcdoc
    const shell = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Gym CAR — Iniciación</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;background:#0a0a0a;overflow:hidden}
.tabs{display:flex;position:fixed;top:0;left:0;right:0;z-index:9;
  background:rgba(8,8,8,.97);backdrop-filter:blur(14px);
  border-bottom:1px solid #242424}
.tab{flex:1;padding:15px 0;background:none;border:none;
  border-bottom:3px solid transparent;font-size:12px;font-weight:700;
  letter-spacing:3px;color:#444;cursor:pointer;
  text-transform:uppercase;transition:.2s}
.tab.on{color:#ff4500;border-bottom-color:#ff4500}
.panels{padding-top:52px;height:100%}
.panel{display:none;height:calc(100% - 52px)}
.panel.on{display:block}
.panel iframe{width:100%;height:100%;border:none;display:block}
</style>
</head>
<body>
<div class="tabs">
  <button class="tab on" onclick="sw(0)" id="t0">DÍA 1</button>
  <button class="tab" onclick="sw(1)" id="t1">DÍA 2</button>
  <button class="tab" onclick="sw(2)" id="t2">DÍA 3</button>
</div>
<div class="panels">
  <div class="panel on" id="p0"><iframe srcdoc="${esc(processed[0])}"></iframe></div>
  <div class="panel" id="p1"><iframe srcdoc="${esc(processed[1])}"></iframe></div>
  <div class="panel" id="p2"><iframe srcdoc="${esc(processed[2])}"></iframe></div>
</div>
<script>
function sw(n){[0,1,2].forEach(i=>{
  document.getElementById('p'+i).classList.toggle('on',i===n);
  document.getElementById('t'+i).classList.toggle('on',i===n);
});}
<\/script>
</body>
</html>`;

    dlBar.style.width = '95%';
    dlStatus.textContent = 'Generando descarga…';

    // 7. Descargar como un solo archivo
    const blob = new Blob([shell], { type: 'text/html; charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'Gym-CAR-Iniciacion.html';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);

    dlBar.style.width = '100%';
    dlStatus.textContent = '¡Listo! 3 días en un solo archivo.';
    setTimeout(() => {
      overlay.classList.remove('active');
      btn.disabled = false;
      btn.textContent = '✓ Descargado';
      setTimeout(() => { btn.textContent = '↓ Descargar todo'; }, 3000);
    }, 1400);

  } catch (err) {
    overlay.classList.remove('active');
    btn.disabled = false;
    if (err.message !== 'cancelled') {
      console.error(err);
      btn.textContent = 'Error — reintentar';
      setTimeout(() => { btn.textContent = '↓ Descargar todo'; }, 3000);
    }
  }
}

async function downloadOffline(dayNum, btn) {
  dlCancelled = false;
  const overlay = document.getElementById('dlOverlay');
  const dlTitle = document.getElementById('dlTitle');
  const dlSub   = document.getElementById('dlSub');
  const dlBar   = document.getElementById('dlBar');
  const dlStatus = document.getElementById('dlStatus');

  dlTitle.textContent = 'DÍA ' + ['', 'UNO', 'DOS', 'TRES'][dayNum];
  dlSub.textContent   = 'Preparando HTML para uso offline…';
  dlBar.style.width   = '0%';
  dlStatus.textContent = 'Descargando página…';
  overlay.classList.add('active');
  btn.disabled = true;

  try {
    // 1. Fetch el HTML del día
    const res = await fetch('gym-dia' + dayNum + '.html');
    if (!res.ok) throw new Error('No se pudo cargar gym-dia' + dayNum + '.html');
    let html = await res.text();

    if (dlCancelled) throw new Error('cancelled');

    // 2. Extraer URLs únicas de imágenes CDN
    const pattern = new RegExp(CDN.replace(/\./g, '\\.').replace(/\//g, '\\/') + '[^"]+\\.gif', 'g');
    const urls = [...new Set(html.match(pattern) || [])];

    if (urls.length === 0) {
      dlStatus.textContent = 'Las imágenes ya están embebidas. Descargando…';
      dlBar.style.width = '100%';
    } else {
      // 3. Descargar y convertir cada imagen a base64
      for (let i = 0; i < urls.length; i++) {
        if (dlCancelled) throw new Error('cancelled');

        const pct = Math.round((i / urls.length) * 85);
        dlBar.style.width = pct + '%';
        dlStatus.textContent = 'Imagen ' + (i + 1) + ' de ' + urls.length + '…';

        try {
          const imgRes = await fetch(urls[i]);
          const blob   = await imgRes.blob();
          const dataUri = await blobToDataUri(blob);
          html = html.split(urls[i]).join(dataUri);
        } catch (e) {
          console.warn('No se pudo cargar:', urls[i]);
        }
      }
      dlBar.style.width = '92%';
    }

    // 4. Actualizar el crédito de fuente
    html = html.replace(
      /Imágenes:.*?CDN/,
      'Imágenes: ExerciseGymGifsDB (embebidas — funciona sin internet)'
    );

    dlStatus.textContent = 'Creando archivo…';
    dlBar.style.width = '98%';

    // 5. Generar descarga
    const blob = new Blob([html], { type: 'text/html; charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'Gym-CAR-Dia' + dayNum + '-Offline.html';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);

    dlBar.style.width = '100%';
    dlStatus.textContent = '¡Listo! Archivo descargado.';

    setTimeout(() => {
      overlay.classList.remove('active');
      btn.disabled = false;
      btn.textContent = '✓ Descargado';
      btn.classList.add('success');
      setTimeout(() => {
        btn.textContent = '↓ Offline';
        btn.classList.remove('success');
      }, 3000);
    }, 1200);

  } catch (err) {
    overlay.classList.remove('active');
    btn.disabled = false;
    if (err.message !== 'cancelled') {
      btn.textContent = 'Error';
      setTimeout(() => { btn.textContent = '↓ Offline'; }, 3000);
      console.error(err);
    }
  }
}
