// ultra.js: the DOM glue for ultra apps written in LPython.
//
// The wasm module calls into the "js" imports below while view() runs; those
// calls build a lightweight vnode tree. After view() returns we diff the new
// tree against the last one and patch the DOM. Events are delegated from the
// mount point and turned into update(msg, arg) calls.

const EVENT = 0;

export async function mount(root, url, opts = {}) {
  if (typeof root === "string") root = document.querySelector(root);

  let mem, ex;
  const td = new TextDecoder();
  const cache = new Map();

  // LPython strings are a pointer to { data: i32, len: i32 }.
  // Literals live in static data, so decoding is cached by (data, len).
  const str = (p) => {
    const dv = new DataView(mem.buffer);
    const a = dv.getInt32(p, true), l = dv.getInt32(p + 4, true);
    const k = a * 4096 + l;
    let s = cache.get(k);
    if (s === undefined) {
      s = td.decode(new Uint8Array(mem.buffer, a, l));
      if (l < 4096) cache.set(k, s);
    }
    return s;
  };

  const K = (k) => (typeof k === "object" ? k.k : str(k)); // storage key

  // ------------------------------------------------------------ string store
  const strs = [""];
  const free = [];
  const sNew = (v = "") => {
    if (free.length) { const h = free.pop(); strs[h] = v; return h; }
    strs.push(v); return strs.length - 1;
  };

  // ------------------------------------------------------------ vnode builder
  // vnode: { t, k, a, cls, p, ev, c, n }   text: { t: "#", s, n }
  let stack, cur;
  const node = (t) => ({ t, k: null, a: null, cls: "", p: null, ev: null, c: [], n: null });
  const push = (v) => cur.c.push(v);
  const txt = (s) => push({ t: "#", k: null, s: String(s), n: null });
  const setA = (k, v) => ((cur.a ||= {})[k] = v);
  const setP = (k, v) => ((cur.p ||= {})[k] = v);
  const setEv = (k, v) => ((cur.ev ||= {})[k] = v);

  // ------------------------------------------------------------ scheduling
  let queued = false;
  const schedule = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(render);
  };
  const dispatch = (msg, arg) => {
    ex.update(msg, arg);
    schedule();
  };

  const js = {
    el: (p) => { const v = node(str(p)); push(v); stack.push(cur); cur = v; },
    end: () => { cur = stack.pop(); },
    text: (p) => txt(str(p)),
    num: (x) => txt(x),
    fnum: (x, d) => txt(x.toFixed(d)),
    text_ref: (h) => txt(strs[h] ?? ""),

    attr: (k, v) => setA(str(k), str(v)),
    attr_num: (k, v) => setA(str(k), String(v)),
    cls: (p) => { const c = str(p); if (c) cur.cls = cur.cls ? cur.cls + " " + c : c; },
    cls_if: (p, on) => { if (on) js.cls(p); },
    key: (k) => { cur.k = k; },
    value_ref: (h) => setP("value", strs[h] ?? ""),
    checked: (on) => setP("checked", !!on),
    autofocus: () => setP("__focus", true),

    on_click: (m, a) => setEv("click", [m, a]),
    on_dblclick: (m, a) => setEv("dblclick", [m, a]),
    on_input: (m) => setEv("input", [m, EVENT]),
    on_enter: (m, a) => setEv("enter", [m, a]),

    after: (ms, m, a) => setTimeout(() => dispatch(m, a), ms),
    now_ms: () => performance.now(),
    log: (x) => console.log("[ultra]", x),

    s_new: () => sNew(),
    s_dup: (h) => sNew(strs[h]),
    s_copy: (d, s) => { strs[d] = strs[s]; },
    s_clear: (h) => { strs[h] = ""; },
    s_free: (h) => { if (h > 0) { strs[h] = ""; free.push(h); } },
    s_len: (h) => (strs[h] ?? "").trim().length,
    s_save: (k, h) => { try { localStorage.setItem(K(k), strs[h]); } catch {} },
    s_load: (k, h) => {
      let v = null;
      try { v = localStorage.getItem(K(k)); } catch {}
      if (v === null) return 0;
      strs[h] = v; return 1;
    },
    store_i32: (k, v) => { try { localStorage.setItem(K(k), String(v)); } catch {} },
    load_i32: (k, d) => {
      let v = null;
      try { v = localStorage.getItem(K(k)); } catch {}
      return v === null ? d : v | 0;
    },
  };

  for (const f of ["s_save", "s_load", "store_i32", "load_i32"]) {
    const base = js[f];
    js[f + "_at"] = (k, i, x) => base({ k: str(k) + "." + i }, x);
  }

  // Minimal WASI so print() works and _start-style exits don't crash.
  const wasi = {
    proc_exit: () => {},
    fd_write: (fd, iovs, n, out) => {
      const dv = new DataView(mem.buffer);
      let s = "", total = 0;
      for (let i = 0; i < n; i++) {
        const p = dv.getInt32(iovs + i * 8, true), l = dv.getInt32(iovs + i * 8 + 4, true);
        s += td.decode(new Uint8Array(mem.buffer, p, l)); total += l;
      }
      (fd === 2 ? console.error : console.log)(s.replace(/\n$/, ""));
      dv.setInt32(out, total, true);
      return 0;
    },
  };

  const imports = { js, wasi_snapshot_preview1: wasi };
  let instance;
  if (typeof url === "string") {
    const res = await fetch(url);
    // Streaming compile needs the application/wasm MIME type; fall back if absent.
    ({ instance } = (res.headers.get("content-type") || "").startsWith("application/wasm")
      ? await WebAssembly.instantiateStreaming(res, imports)
      : await WebAssembly.instantiate(await res.arrayBuffer(), imports));
  } else {
    ({ instance } = await WebAssembly.instantiate(url, imports));
  }
  ex = instance.exports;
  mem = ex.memory;

  // ------------------------------------------------------------ diff / patch
  const create = (v) => {
    if (v.t === "#") return (v.n = document.createTextNode(v.s));
    const n = (v.n = document.createElement(v.t));
    if (v.cls) n.className = v.cls;
    if (v.a) for (const k in v.a) n.setAttribute(k, v.a[k]);
    if (v.p) setProps(n, null, v.p);
    n.__ev = v.ev;
    for (const c of v.c) n.appendChild(create(c));
    return n;
  };

  const setProps = (n, o, p) => {
    for (const k in p) {
      if (k === "__focus") { if (!o || !o.__focus) queueMicrotask(() => n.focus()); continue; }
      if (n[k] !== p[k]) n[k] = p[k];
    }
  };

  const patch = (o, v) => {
    if (o.t !== v.t || o.k !== v.k) {
      const n = create(v);
      o.n.replaceWith(n);
      return;
    }
    const n = (v.n = o.n);
    if (v.t === "#") { if (o.s !== v.s) n.data = v.s; return; }
    if (o.cls !== v.cls) n.className = v.cls;
    if (o.a !== v.a) {
      const oa = o.a || {}, va = v.a || {};
      for (const k in oa) if (!(k in va)) n.removeAttribute(k);
      for (const k in va) if (oa[k] !== va[k]) n.setAttribute(k, va[k]);
    }
    if (v.p) setProps(n, o.p, v.p);
    n.__ev = v.ev;
    patchChildren(n, o.c, v.c);
  };

  const patchChildren = (parent, oc, vc) => {
    if (oc.length === 0 && vc.length === 0) return;
    const keyed = vc.length > 0 && vc[0].k !== null && oc.length > 0 && oc[0].k !== null;
    if (!keyed) {
      const m = Math.min(oc.length, vc.length);
      for (let i = 0; i < m; i++) patch(oc[i], vc[i]);
      for (let i = m; i < vc.length; i++) parent.appendChild(create(vc[i]));
      for (let i = m; i < oc.length; i++) oc[i].n.remove();
      return;
    }
    const byKey = new Map();
    for (const o of oc) byKey.set(o.k, o);
    let ref = parent.firstChild;
    for (const v of vc) {
      const o = byKey.get(v.k);
      if (o) { byKey.delete(v.k); patch(o, v); } else create(v);
      if (v.n !== ref) parent.insertBefore(v.n, ref);
      else ref = ref.nextSibling;
    }
    for (const o of byKey.values()) o.n.remove();
  };

  // ------------------------------------------------------------ render
  let prev = null;
  function render() {
    queued = false;
    const top = node("#root");
    stack = []; cur = top;
    ex.view();
    if (prev === null) {
      root.textContent = "";
      for (const c of top.c) root.appendChild(create(c));
    } else {
      patchChildren(root, prev.c, top.c);
    }
    prev = top;
  }

  // ------------------------------------------------------------ events
  const find = (t, kind) => {
    for (let n = t; n && n !== root; n = n.parentNode) if (n.__ev && n.__ev[kind]) return n.__ev[kind];
    return null;
  };
  const on = (type, kind, pre) =>
    root.addEventListener(type, (e) => {
      if (pre && !pre(e)) return;
      const h = find(e.target, kind);
      if (!h) return;
      if (kind === "input") strs[EVENT] = e.target.value;
      dispatch(h[0], h[1]);
    });
  on("click", "click");
  on("dblclick", "dblclick");
  on("input", "input");
  on("keydown", "enter", (e) => e.key === "Enter" && !e.isComposing);

  // Run module-level code (which calls init()), then first render.
  ex.__main__global_stmts();
  render();
  return { dispatch, render, exports: ex };
}
