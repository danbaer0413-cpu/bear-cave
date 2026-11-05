/* Bear Cave standalone runtime.
   Gives the dashboard page the same small API it uses inside Claude: dash.data, dash.draw, dash.calc,
   dash.params / setParams / setLink, dash.onData and dash.colors. Datasets are the CSV / JSON files in data/,
   listed in data/manifest.json; they load the first time a visible chart needs them. Choices live in the URL. */
(function () {
  const manifest = { datasets: {} };
  const store = {};          // name -> {status, data}
  const calcs = {};          // name -> {inputs, fn, value}
  const draws = [];          // [name, fn]
  const onData = [];
  let params = {};
  const readURL = () => { const q = new URLSearchParams(location.search); const p = {}; for (const [k, v] of q) p[k] = v; return p; };
  params = readURL();
  const writeURL = () => {
    const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null && v !== ''));
    const s = q.toString();
    history.replaceState(null, '', location.pathname + (s ? '?' + s : '') + location.hash);
  };
  const sources = (name) => calcs[name] ? calcs[name].inputs.flatMap(sources) : [name];
  let ready = false;   // the data file list (manifest) has loaded
  function load(name) {
    if (!ready || store[name]) return;
    const m = manifest.datasets[name];
    if (!m) { store[name] = { status: 'error' }; return; }
    store[name] = { status: 'loading' };
    fetch('data/' + m.file + '?v=' + (manifest.built || ''))
      .then((r) => { if (!r.ok) throw new Error(r.status); return m.file.endsWith('.json') ? r.json() : r.text(); })
      .then((d) => { store[name] = { status: 'ok', data: typeof d === 'string' ? d3.csvParse(d) : d }; schedule(); })
      .catch((e) => { console.error('load', name, e); store[name] = { status: 'error' }; schedule(); });
  }
  function data(name) {
    const c = calcs[name];
    if (c) {
      if (c.value) return { status: 'ok', data: c.value };
      const ins = c.inputs.map(data);
      const bad = ins.find((g) => g.status !== 'ok');
      if (bad) return { status: bad.status };
      try { c.value = c.fn(...ins.map((g) => g.data)); } catch (e) { console.error(name, e); return { status: 'error' }; }
      return { status: 'ok', data: c.value };
    }
    load(name);
    return store[name] || { status: 'loading' };
  }
  let pending = false;
  function schedule() { if (!pending) { pending = true; requestAnimationFrame(render); } }
  function visible(el) { return !el.closest('[hidden]'); }
  function render() {
    pending = false;
    for (const f of onData) { try { f(); } catch (e) { console.error(e); } }
    for (const [name, fn] of draws) {
      for (const el of document.querySelectorAll('[data-draw="' + name + '"]')) {
        if (!visible(el)) continue;
        const srcs = (el.dataset.source || '').split(/\s+/).filter(Boolean);
        const st = srcs.map(data);
        if (st.some((g) => g.status === 'loading')) { if (!el.childElementCount && !el.textContent.trim()) el.textContent = 'Loading…'; continue; }
        try { fn(el); } catch (e) { console.error('draw', name, e); }
      }
    }
  }
  window.dash = {
    colors: ['#2a78d6', '#e2731b', '#2c9f6b', '#8a5cd1', '#c0392b', '#8c6d1f', '#1f8a99', '#c2185b'],
    data, draw: (name, fn) => { draws.push([name, fn]); schedule(); },
    calc: (name, def) => { calcs[name] = { inputs: def.inputs, fn: def.fn }; },
    params: () => ({ ...params }),
    setParams: (p) => { params = { ...params, ...p }; writeURL(); schedule(); },
    setLink: (h) => { history.replaceState(null, '', location.pathname + location.search + '#' + h); },
    onData: (f) => { onData.push(f); schedule(); },
  };
  window.addEventListener('resize', () => { clearTimeout(window.__rz); window.__rz = setTimeout(schedule, 150); });
  window.addEventListener('popstate', () => { params = readURL(); schedule(); });
  fetch('data/manifest.json', { cache: 'no-store' }).then((r) => r.json()).then((m) => {
    Object.assign(manifest, m); ready = true;
    const el = document.getElementById('bc-updated');
    if (el && m.updated) el.textContent = 'Data updated ' + new Date(m.updated).toLocaleString('en-US', { timeZone: 'America/New_York', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) + ' ET';
    schedule();
  });
})();
