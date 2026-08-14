const CDN = 'https://cdn.jsdelivr.net/gh/JahelCuadrado/ExerciseGymGifsDB@v1.1.0/';
let dlCancelled = false;

function cancelDownload() {
  dlCancelled = true;
  document.getElementById('dlOverlay').classList.remove('active');
}

async function blobToDataUri(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload  = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

function extractBody(html) {
  const m = html.match(/<body[^>]*>([\s\S]*)<\/body>/i);
  return m ? m[1] : html;
}

function extractDataTotal(html) {
  const m = html.match(/data-total="(\d+)"/);
  return m ? parseInt(m[1], 10) : 10;
}

function namespaceDayHtml(bodyHtml, n) {
  return bodyHtml
    .replace(/\bid="([\w-]+)"/g,            (_, id) => `id="d${n}-${id}"`)
    .replace(/onclick="toggleCardio\(\)"/g,                  `onclick="day${n}TC()"`)
    .replace(/onclick="toggleCard\(event,(\d+)\)"/g, (_, i) => `onclick="day${n}T(event,${i})"`);
}

function makeDayScript(n, total) {
  return `(function(){
  var P='d${n}-',TOTAL=${total},done=new Set();
  function markBtn(btn,isDone){
    btn.style.color=isDone?'white':'transparent';
    btn.style.background=isDone?'#4a9a4a':'transparent';
    btn.style.borderColor=isDone?'#4a9a4a':'#2a2a2a';
  }
  function updateProgress(){
    var n=done.size;
    document.getElementById(P+'progressBar').style.width=(n/TOTAL*100)+'%';
    document.getElementById(P+'countDisplay').textContent=n+' / '+TOTAL;
    document.getElementById(P+'completeBanner').classList.toggle('show',n===TOTAL);
  }
  window['day${n}TC']=function(){
    var card=document.getElementById(P+'cardio');
    if(!card)return;
    var btn=document.getElementById(P+'cardioCheck');
    var isDone=card.classList.toggle('done');
    markBtn(btn,isDone);
    isDone?done.add('c'):done.delete('c');
    updateProgress();
  };
  var openDetail=null;
  window['day${n}T']=function(e,idx){
    var btn=document.getElementById(P+'check'+idx);
    if(e.target===btn||btn.contains(e.target)){
      e.stopPropagation();
      var card=document.getElementById(P+'ex'+idx);
      var isDone=card.classList.toggle('done');
      markBtn(btn,isDone);
      if(isDone){done.add(idx);card.classList.add('just-done');setTimeout(function(){card.classList.remove('just-done');},300);}
      else{done.delete(idx);}
      updateProgress();
      return;
    }
    var detail=document.getElementById(P+'detail'+idx);
    if(openDetail&&openDetail!==detail)openDetail.classList.remove('open');
    detail.classList.toggle('open');
    openDetail=detail.classList.contains('open')?detail:null;
  };
})();`;
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
  dlStatus.textContent = 'Cargando páginas y recursos…';
  overlay.classList.add('active');
  btn.disabled = true;

  try {
    // 1. Fetch CSS, JS y los 3 HTMLs en paralelo
    const [dayCss, dayJs, ...htmls] = await Promise.all([
      fetch('css/day.css').then(r => { if (!r.ok) throw new Error('css/day.css'); return r.text(); }),
      fetch('js/day.js').then(r => { if (!r.ok) throw new Error('js/day.js'); return r.text(); }),
      ...[1, 2, 3].map(d =>
        fetch('gym-dia' + d + '.html').then(r => {
          if (!r.ok) throw new Error('gym-dia' + d + '.html');
          return r.text();
        })
      )
    ]);
    if (dlCancelled) throw new Error('cancelled');

    // 2. Recolectar todas las URLs únicas de GIF entre los 3 días
    const cdnRe  = new RegExp(CDN.replace(/\./g, '\\.').replace(/\//g, '\\/') + '[^"]+\\.gif', 'g');
    const allUrls = [...new Set(htmls.flatMap(h => h.match(cdnRe) || []))];
    const total   = allUrls.length;
    dlStatus.textContent = total + ' imágenes únicas — descargando…';

    // 3. Descargar cada GIF una sola vez → mapa URL→base64
    const b64Map = {};
    for (let i = 0; i < allUrls.length; i++) {
      if (dlCancelled) throw new Error('cancelled');
      dlBar.style.width    = Math.round((i / total) * 75) + '%';
      dlStatus.textContent = 'Imagen ' + (i + 1) + ' / ' + total + '…';
      try {
        const blob = await fetch(allUrls[i]).then(r => r.blob());
        b64Map[allUrls[i]] = await blobToDataUri(blob);
      } catch (e) { console.warn('No se pudo cargar:', allUrls[i]); }
    }

    dlBar.style.width    = '80%';
    dlStatus.textContent = 'Ensamblando archivo…';

    // 4. Para cada día: reemplazar GIFs + extraer body + namespaciar IDs
    const dayTotals = htmls.map(extractDataTotal);
    const dayBodies = htmls.map((html, i) => {
      let h = html;
      for (const [url, b64] of Object.entries(b64Map)) h = h.split(url).join(b64);
      h = h.replace(/Imágenes:.*?CDN/, 'Imágenes: ExerciseGymGifsDB (embebidas)');
      return namespaceDayHtml(extractBody(h), i + 1);
    });

    dlBar.style.width    = '90%';
    dlStatus.textContent = 'Generando HTML final…';

    // 5. Construir el archivo combinado como una sola página (sin iframes)
    const shell = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Gym CAR — Iniciación</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
.tabs{display:flex;position:fixed;top:0;left:0;right:0;z-index:200;
  background:rgba(8,8,8,.97);backdrop-filter:blur(14px);
  border-bottom:1px solid #242424}
.tab{flex:1;padding:15px 0;background:none;border:none;
  border-bottom:3px solid transparent;font-size:12px;font-weight:700;
  letter-spacing:3px;color:#444;cursor:pointer;
  text-transform:uppercase;transition:.2s;font-family:inherit}
.tab.on{color:#ff4500;border-bottom-color:#ff4500}
.panels{padding-top:52px}
.panel{display:none}
.panel.on{display:block}
${dayCss}
.progress-wrap{top:52px}
body{padding-bottom:0}
</style>
</head>
<body>
<div class="tabs">
  <button class="tab on" onclick="sw(0)">DÍA 1</button>
  <button class="tab"    onclick="sw(1)">DÍA 2</button>
  <button class="tab"    onclick="sw(2)">DÍA 3</button>
</div>
<div class="panels">
  <div class="panel on" id="panel0">${dayBodies[0]}</div>
  <div class="panel"    id="panel1">${dayBodies[1]}</div>
  <div class="panel"    id="panel2">${dayBodies[2]}</div>
</div>
<script>
function sw(n){[0,1,2].forEach(function(i){
  document.getElementById('panel'+i).classList.toggle('on',i===n);
  document.querySelectorAll('.tab')[i].classList.toggle('on',i===n);
});}
${makeDayScript(1, dayTotals[0])}
${makeDayScript(2, dayTotals[1])}
${makeDayScript(3, dayTotals[2])}
<\/script>
</body>
</html>`;

    dlBar.style.width    = '95%';
    dlStatus.textContent = 'Generando descarga…';

    const blob = new Blob([shell], { type: 'text/html; charset=utf-8' });
    const a    = document.createElement('a');
    a.href     = URL.createObjectURL(blob);
    a.download = 'Gym-CAR-Iniciacion.html';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);

    dlBar.style.width    = '100%';
    dlStatus.textContent = '¡Listo! 3 días en un solo archivo.';
    setTimeout(() => {
      overlay.classList.remove('active');
      btn.disabled    = false;
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
  const overlay  = document.getElementById('dlOverlay');
  const dlTitle  = document.getElementById('dlTitle');
  const dlSub    = document.getElementById('dlSub');
  const dlBar    = document.getElementById('dlBar');
  const dlStatus = document.getElementById('dlStatus');

  dlTitle.textContent  = 'DÍA ' + ['', 'UNO', 'DOS', 'TRES'][dayNum];
  dlSub.textContent    = 'Preparando HTML para uso offline…';
  dlBar.style.width    = '0%';
  dlStatus.textContent = 'Descargando recursos…';
  overlay.classList.add('active');
  btn.disabled = true;

  try {
    // 1. Fetch HTML, CSS y JS en paralelo
    const [html0, css, js] = await Promise.all([
      fetch('gym-dia' + dayNum + '.html').then(r => {
        if (!r.ok) throw new Error('gym-dia' + dayNum + '.html');
        return r.text();
      }),
      fetch('css/day.css').then(r => r.text()),
      fetch('js/day.js').then(r => r.text()),
    ]);
    if (dlCancelled) throw new Error('cancelled');

    // 2. Inline CSS y JS (las rutas relativas no funcionan en un archivo local)
    let html = html0
      .replace(/<link[^>]+href="css\/day\.css"[^>]*>/i, '<style>\n' + css + '\n</style>')
      .replace(/<script[^>]+src="js\/day\.js"[^>]*><\/script>/i, '<script>\n' + js + '\n<\/script>');

    // 3. Extraer URLs únicas de GIFs CDN
    const pattern = new RegExp(CDN.replace(/\./g, '\\.').replace(/\//g, '\\/') + '[^"]+\\.gif', 'g');
    const urls    = [...new Set(html.match(pattern) || [])];

    if (urls.length === 0) {
      dlBar.style.width    = '95%';
      dlStatus.textContent = 'Sin imágenes CDN. Descargando…';
    } else {
      // 4. Descargar GIFs y reemplazar con base64
      for (let i = 0; i < urls.length; i++) {
        if (dlCancelled) throw new Error('cancelled');
        dlBar.style.width    = Math.round((i / urls.length) * 88) + '%';
        dlStatus.textContent = 'Imagen ' + (i + 1) + ' de ' + urls.length + '…';
        try {
          const blob    = await fetch(urls[i]).then(r => r.blob());
          const dataUri = await blobToDataUri(blob);
          html = html.split(urls[i]).join(dataUri);
        } catch (e) { console.warn('No se pudo cargar:', urls[i]); }
      }
      dlBar.style.width = '92%';
    }

    // 5. Actualizar crédito
    html = html.replace(
      /Imágenes:.*?CDN/,
      'Imágenes: ExerciseGymGifsDB (embebidas — funciona sin internet)'
    );

    dlStatus.textContent = 'Creando archivo…';
    dlBar.style.width    = '98%';

    const blob = new Blob([html], { type: 'text/html; charset=utf-8' });
    const a    = document.createElement('a');
    a.href     = URL.createObjectURL(blob);
    a.download = 'Gym-CAR-Dia' + dayNum + '-Offline.html';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);

    dlBar.style.width    = '100%';
    dlStatus.textContent = '¡Listo! Archivo descargado.';

    setTimeout(() => {
      overlay.classList.remove('active');
      btn.disabled    = false;
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
