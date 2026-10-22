(function () {
  // Index: search + filters
  var q = document.getElementById('q');
  if (q) {
    var state = { v: false, t: false, m: false };
    var trips = Array.prototype.slice.call(document.querySelectorAll('.trip'));
    var years = Array.prototype.slice.call(document.querySelectorAll('.year'));
    var count = document.getElementById('count');
    var empty = document.getElementById('empty');
    var plural = function (n, a, b, c) { var m10 = n % 10, m100 = n % 100; return m10 == 1 && m100 != 11 ? a : m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20) ? b : c; };
    function apply() {
      var s = q.value.trim().toLowerCase(), shown = 0;
      trips.forEach(function (li) {
        var f = li.getAttribute('data-f');
        var ok = (!s || li.getAttribute('data-q').indexOf(s) >= 0) &&
          (!state.v || f.indexOf('v') >= 0) && (!state.t || f.indexOf('t') >= 0) && (!state.m || f.indexOf('m') >= 0);
        li.hidden = !ok; if (ok) shown++;
      });
      years.forEach(function (y) {
        var n = y.querySelectorAll('.trip:not([hidden])').length;
        y.hidden = n === 0;
      });
      if (count) count.textContent = shown + ' из ' + trips.length;
      empty.hidden = shown > 0;
    }
    q.addEventListener('input', apply);
    document.querySelectorAll('.chip').forEach(function (c) {
      c.addEventListener('click', function () {
        var k = c.getAttribute('data-k'); state[k] = !state[k];
        c.setAttribute('aria-pressed', String(state[k])); apply();
      });
    });
  }

  // Home: latest-trips carousel
  var track = document.querySelector('.feats'), cp = document.querySelector('.cprev'), cn = document.querySelector('.cnext');
  if (track && cp && cn) {
    function step() { var it = track.children[0]; return it ? it.getBoundingClientRect().width + parseFloat(getComputedStyle(track).columnGap || 18) : track.clientWidth; }
    function upd() { cp.disabled = track.scrollLeft <= 2; cn.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 2; }
    cp.addEventListener('click', function () { track.scrollBy({ left: -step(), behavior: 'smooth' }); });
    cn.addEventListener('click', function () { track.scrollBy({ left: step(), behavior: 'smooth' }); });
    track.addEventListener('scroll', function () { window.requestAnimationFrame(upd); }, { passive: true });
    track.addEventListener('keydown', function (ev) { if (ev.key === 'ArrowRight') { ev.preventDefault(); cn.click(); } else if (ev.key === 'ArrowLeft') { ev.preventDefault(); cp.click(); } });
    window.addEventListener('resize', upd); upd();
  }

  // Trip page: click-to-play YouTube (no YouTube scripts load until the reader asks)
  // Video source: Дзен (default) / YouTube
  function vsrc() { return document.documentElement.getAttribute('data-vsrc') || 'dzen'; }
  function stopAll() {
    document.querySelectorAll('.yt').forEach(function (box) {
      if (box.querySelector('iframe') && box.getAttribute('data-orig') !== null) { box.innerHTML = box.getAttribute('data-orig'); bindYt(box); }
    });
  }
  window.__stopDzen = stopAll;
  function bindYt(box) {
    var btn = box.querySelector('.ytplay');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var id = box.getAttribute('data-id'), list = box.getAttribute('data-list'), dz = box.getAttribute('data-dzen');
      var useDz = dz && (vsrc() !== 'yt' || (!id && !list));
      var src = useDz ? 'https://dzen.ru/embed/' + dz + '?from_block=partner&from=zen&mute=0&autoplay=1&tv=0'
              : id ? 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0&enablejsapi=1'
                   : 'https://www.youtube-nocookie.com/embed/videoseries?list=' + list + '&autoplay=1&enablejsapi=1';
      var f = document.createElement('iframe');
      f.src = src; f.title = 'Видео'; f.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen';
      f.allowFullscreen = true;
      box.setAttribute('data-orig', box.innerHTML);
      box.innerHTML = ''; box.appendChild(f);
    });
  }
  document.querySelectorAll('.yt').forEach(bindYt);
  var sw = document.querySelector('.vsrc');
  if (sw) {
    var dzBtn = sw.querySelector('[data-src="dzen"]');
    var saved = null;
    try { saved = localStorage.getItem('vsrc'); } catch (e) {}
    function setSrc(m, save) {
      if (m === 'dzen' && dzBtn.disabled) m = 'yt';
      document.documentElement.setAttribute('data-vsrc', m);
      sw.querySelectorAll('button').forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-src') === m)); });
      if (save) { try { localStorage.setItem('vsrc', m); } catch (e) {} }
    }
    setSrc(saved === 'yt' ? 'yt' : 'dzen', false);
    sw.querySelectorAll('button').forEach(function (b) {
      b.addEventListener('click', function () { if (b.disabled) return; stopAll(); setSrc(b.getAttribute('data-src'), true); });
    });
  }

  // Home: world map (Leaflet + site-coloured layers), loaded when it nears the viewport
  var wm = document.querySelector('.worldmap');
  if (wm) {
    var wmDone = false;
    var CDN = ((document.querySelector('link[href*="assets/style.css"]') || {}).getAttribute ? document.querySelector('link[href*="assets/style.css"]').getAttribute('href').replace(/style\.css.*$/, '') : 'assets/') + 'vendor/leaflet/';  // Leaflet 1.9.4, self-hosted (no CDN)
    function loadCss(h) { var l = document.createElement('link'); l.rel = 'stylesheet'; l.href = h; document.head.appendChild(l); }
    function loadJs(src, cb) { var sc = document.createElement('script'); sc.src = src; sc.onload = function () { cb(); }; sc.onerror = function () { cb(new Error('load')); }; document.head.appendChild(sc); }
    function css(v) { return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }
    function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
    function build() {
      var box = document.getElementById('worldmap');
      var base = (document.querySelector('link[href*="assets/style.css"]').getAttribute('href') || '').replace(/style\.css.*$/, '');
      var ver = (document.querySelector('script[src*="site.js"]').src.split('v=')[1] || '');
      function need(name, file) { return new Promise(function (ok, no) { if (window[name]) return ok(); loadJs(base + file + '?v=' + ver, function (e) { e ? no(e) : ok(); }); }); }
      need('__WM', 'map-data.js').then(function () {
        var d = [window.__WM.k, window.__WM.c];
        box.innerHTML = '';
        var dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        var map = L.map(box, { zoomSnap: 0.25, minZoom: 1, worldCopyJump: true, attributionControl: true, scrollWheelZoom: false });
        map.on('focus', function () { map.scrollWheelZoom.enable(); });
        map.on('blur', function () { map.scrollWheelZoom.disable(); });
        var acc = css('--accent'), surf = css('--surface');
        map.createPane('land'); map.getPane('land').style.zIndex = 250;
        need('__WW', 'map-world.js').then(function () {  // land/borders arrive later; points and countries show first
          L.geoJSON(window.__WW.land, { pane: 'land', interactive: false, attribution: 'Natural Earth', style: { stroke: false, fillColor: css('--map-land'), fillOpacity: 1 } }).addTo(map);
          L.geoJSON(window.__WW.borders, { pane: 'land', interactive: false, style: { color: css('--map-border'), weight: .7, opacity: 1, fill: false } }).addTo(map);
        }, function () {});
        var countries = L.geoJSON(d[0], {
          style: { color: acc, weight: 1, opacity: .55, fillColor: acc, fillOpacity: dark ? .28 : .2 }, interactive: false
        }).addTo(map);
        var CN = window.__WM.cn || {}, flagBase = base + 'flags/';
        function host(u) {
          try {
            return new URL(u).hostname.replace(/^www\./, '').split('.').map(function (l) { try { return /^xn--/i.test(l) ? puny(l.slice(4).toLowerCase()) : l; } catch (e) { return l; } }).join('.');
          } catch (e) { return u; }
        }
        function card(c) {
          var h = '<div class="wm-pop"><div class="wm-img"></div><div class="wm-body"><b>' + esc(c.n) + '</b>';
          h += '<div class="wm-meta">' + (c.c ? '<span class="wm-c"><img src="' + flagBase + c.c + '.svg" alt="" width="16" height="12">' + esc(CN[c.c] || '') + '</span>' : '') + '</div>';
          h += '<div class="wm-ext"></div></div>';
          h += '<div class="wm-last">' + (c.y || c.s ? '<span class="wm-lbl">Последнее посещение</span><div class="wm-row">' + (c.y ? '<span class="wm-y">' + esc(c.y) + '</span>' : '') +
            (c.s ? '<a class="wm-trip" href="trips/' + esc(c.s) + '.html" target="_blank" rel="noopener" title="' + esc(c.t) + '">' + esc(c.t) + ' →</a>' : '') + '</div>' : '') + '</div>';
          return h + '</div>';
        }
        function fill(el, w) {
          if (!el || !w) return;
          if (w.img) { var im = new Image(); im.alt = ''; im.onload = function () { im.classList.add('on'); }; im.src = w.img; el.querySelector('.wm-img').appendChild(im); }
          var ext = [];
          if (w.url) ext.push('<a href="' + esc(w.url) + '" target="_blank" rel="noopener">Википедия</a>');
          if (w.site) ext.push('<a href="' + esc(w.site) + '" target="_blank" rel="noopener">' + esc(host(w.site)) + '</a>');
          el.querySelector('.wm-ext').innerHTML = ext.join('<span>·</span>');
        }
        var pts = d[1].map(function (c) {
          var m = L.circleMarker([c.la, c.lo], { radius: 6, weight: 1.5, color: surf, fillColor: acc, fillOpacity: 1 });
          m.bindPopup(card(c), { closeButton: false, className: 'wm-popup', offset: [0, -2], maxWidth: 260, minWidth: 260, autoPanPadding: [16, 16] });
          m.on('popupopen', function (ev) {
            var el = ev.popup.getElement().querySelector('.wm-pop');
            if (el.getAttribute('data-f')) return; el.setAttribute('data-f', '1');
            if (c.wi) fill(el, { img: c.wi.img ? base + 'cities/' + c.wi.img : '', url: c.wi.url, site: c.wi.site });
          });
          m.on('popupclose', function (ev) {
            ev.popup.setContent(card(c));
            // Leaflet hides a marker's permanent label while its popup is open; bring it back
            setTimeout(function () { var t = m.getTooltip(); if (t && t.options.permanent && !m.isTooltipOpen()) { m.openTooltip(); schedulePlace(); } }, 0);
          });
          m._wmName = esc(c.n);
          return m;
        });
        var cities = L.featureGroup(pts).addTo(map);
        // City names: hover tooltips when zoomed out, permanent labels from zoom 6
        var LABEL_ZOOM = 6, labelsOn = null;
        function setLabels() {
          var z = map.getZoom();
          var r = Math.max(6, Math.min(11, 6 + (z - 4) * 1.25));   // dots grow from zoom 4
          pts.forEach(function (m) { m.setRadius(r); });
          box.style.setProperty('--wm-lbl', Math.max(12, Math.min(17, 12 + (z - LABEL_ZOOM) * 1.25)) + 'px');
          var on = z >= LABEL_ZOOM;
          var key = on + ':' + Math.round(r);
          if (key === labelsOn) return; labelsOn = key;
          pts.forEach(function (m) {
            m.unbindTooltip();
            m.bindTooltip(m._wmName, on ? { permanent: true, direction: 'right', offset: [Math.round(r) + 2, 0], className: 'wm-label' }
                                        : { direction: 'top', offset: [0, -6], className: 'wm-tip' });
          });
        }
        // Nudge permanent labels up/down (or to the left) so they don't overlap each other or other dots
        var placeTimer = null;
        function placeLabels() {
          if (!labelsOn || labelsOn.indexOf('true') !== 0) return;
          var size = map.getSize(), placed = [], dots = [];
          var vis = pts.filter(function (m) { var p = map.latLngToContainerPoint(m.getLatLng()); m._wmP = p; return p.x > -150 && p.y > -40 && p.x < size.x + 150 && p.y < size.y + 40; });
          vis.forEach(function (m) { var r = m.getRadius(); dots.push({ l: m._wmP.x - r, t: m._wmP.y - r, r: m._wmP.x + r, b: m._wmP.y + r }); });
          vis.sort(function (a, b) { return a._wmP.y - b._wmP.y || a._wmP.x - b._wmP.x; });
          function hit(bx, list) { for (var i = 0; i < list.length; i++) { var o = list[i]; if (bx.l < o.r && bx.r > o.l && bx.t < o.b && bx.b > o.t) return true; } return false; }
          vis.forEach(function (m) {
            var tt = m.getTooltip(), el = tt && tt.getElement(); if (!el) return;
            el.style.marginTop = '0px'; el.style.marginLeft = '0px';
            var w = el.offsetWidth, h = el.offsetHeight, r = m.getRadius(), p = m._wmP, gap = Math.round(r) + 2;
            var cands = [[0, 1], [-h * .6, 1], [h * .6, 1], [-h * 1.1, 1], [h * 1.1, 1], [0, -1], [-h * .6, -1], [h * .6, -1], [-h * 1.1, -1], [h * 1.1, -1]];
            var best = null;
            for (var i = 0; i < cands.length; i++) {
              var dy = cands[i][0], side = cands[i][1];
              var l = side > 0 ? p.x + gap : p.x - gap - w, t = p.y - h / 2 + dy;
              var bx = { l: l, t: t, r: l + w, b: t + h };
              if (!hit(bx, placed) && !hit(bx, dots)) { best = [dy, side, bx]; break; }
              if (!best) best = [dy, side, bx, true];
            }
            if (best[3]) { var l0 = p.x + gap, t0 = p.y - h / 2; best = [0, 1, { l: l0, t: t0, r: l0 + w, b: t0 + h }]; }
            el.style.marginTop = Math.round(best[0]) + 'px';
            el.style.marginLeft = best[1] > 0 ? '0px' : (-(w + 2 * gap)) + 'px';
            placed.push(best[2]);
          });
        }
        function schedulePlace() { clearTimeout(placeTimer); placeTimer = setTimeout(placeLabels, 60); }
        map.on('zoomend', setLabels);
        map.on('zoomend moveend', schedulePlace);
        map.fitBounds([[-8, -166], [78, 190]], { padding: [0, 0] });
        setLabels();
      }).catch(function (er) { if (window.console) console.error(er); box.innerHTML = '<span class="maploading">Не удалось загрузить карту</span>'; });
    }
    function start() {
      if (wmDone) return; wmDone = true;
      if (window.L) return build();
      loadCss(CDN + 'leaflet.css');
      loadJs(CDN + 'leaflet.js', function (err) { if (err) { document.getElementById('worldmap').innerHTML = '<span class="maploading">Не удалось загрузить карту</span>'; return; } build(); });
    }
    if ('IntersectionObserver' in window) {
      var wio = new IntersectionObserver(function (es) { if (es.some(function (e) { return e.isIntersecting; })) { wio.disconnect(); start(); } }, { rootMargin: '300px' });
      wio.observe(wm);
    } else start();
  }

  // Trip page: tabs (Заметки / Фото / Видео / Карта)
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.tab'));
  if (tabs.length) {
    var tabwrap = document.querySelector('.tabwrap');
    function loadMap(panel) {
      panel.querySelectorAll('.mapbox').forEach(function (box) {
        if (box.querySelector('iframe')) return;
        var f = document.createElement('iframe');
        f.src = 'https://www.google.com/maps/d/embed?mid=' + encodeURIComponent(box.getAttribute('data-mid'));
        f.title = 'Карта маршрута';
        box.innerHTML = ''; box.appendChild(f);
      });
    }
    function pauseVideos() {
      document.querySelectorAll('video').forEach(function (v) { try { v.pause(); } catch (e) {} });
      if (window.__stopDzen) window.__stopDzen();
      document.querySelectorAll('.yt iframe').forEach(function (f) {
        try { f.contentWindow.postMessage('{"event":"command","func":"pauseVideo","args":""}', '*'); } catch (e) {}
      });
    }
    function show(key, scroll) {
      var found = false;
      tabs.forEach(function (t) {
        var on = t.getAttribute('href') === '#' + key;
        if (on) found = true;
        t.setAttribute('aria-selected', String(on));
        var p = document.getElementById(t.getAttribute('aria-controls'));
        if (!on && key !== 'video' && p.id === 'p-video') pauseVideos();
        p.hidden = !on;
        if (on && key === 'map') loadMap(p);
      });
      if (!found) return false;
      var tt = tabwrap ? parseFloat(getComputedStyle(tabwrap).top) || 0 : 0;
      if (scroll && tabwrap && tabwrap.getBoundingClientRect().top < tt) {
        window.scrollTo(0, window.scrollY + tabwrap.getBoundingClientRect().top - tt);
      }
      return true;
    }
    tabs.forEach(function (t) {
      t.addEventListener('click', function (ev) {
        ev.preventDefault();
        var key = t.getAttribute('href').slice(1);
        show(key, true);
        try { history.replaceState(null, '', key === 'notes' ? location.pathname : '#' + key); } catch (e) {}
      });
    });
    var h = location.hash.slice(1);
    if (h && !show(h, false) && !document.getElementById(h)) show(tabs[0].getAttribute('href').slice(1), false);
  }

  // Photo lightbox
  var gis = Array.prototype.slice.call(document.querySelectorAll('.gi'));
  if (gis.length) {
    var arrow = function (d) { return '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2"><path d="' + d + '"/></svg>'; };
    var lb = document.createElement('div');
    lb.className = 'lb'; lb.hidden = true; lb.setAttribute('role', 'dialog'); lb.setAttribute('aria-modal', 'true'); lb.setAttribute('aria-label', 'Просмотр фото');
    lb.innerHTML = '<div class="lb-top"><span class="lb-n"></span><button type="button" class="close" aria-label="Закрыть">' + arrow('M5 5l10 10M15 5L5 15') + '</button></div>' +
      '<div class="lb-stage"><img alt=""><button type="button" class="prev" aria-label="Предыдущее фото">' + arrow('M12 4l-6 6 6 6') + '</button><button type="button" class="next" aria-label="Следующее фото">' + arrow('M8 4l6 6-6 6') + '</button></div>' +
      '<div class="lb-cap"></div>';
    document.body.appendChild(lb);
    var img = lb.querySelector('img'), cap = lb.querySelector('.lb-cap'), num = lb.querySelector('.lb-n'), cur = 0, last = null;
    var pre = function (i) { if (i >= 0 && i < gis.length) { var im = new Image(); im.src = gis[i].href; } };
    function go(i) {
      cur = (i + gis.length) % gis.length;
      var a = gis[cur];
      img.src = a.href; img.alt = a.querySelector('img').alt;
      cap.textContent = a.getAttribute('data-c') || '';
      num.textContent = (cur + 1) + ' / ' + gis.length;
      pre(cur + 1); pre(cur - 1);
    }
    function open(i) { last = document.activeElement; lb.hidden = false; document.body.classList.add('lb-open'); go(i); lb.querySelector('.close').focus(); }
    function close() { lb.hidden = true; document.body.classList.remove('lb-open'); img.removeAttribute('src'); if (last) last.focus(); }
    gis.forEach(function (a, i) { a.addEventListener('click', function (ev) { ev.preventDefault(); open(i); }); });
    lb.querySelector('.close').addEventListener('click', close);
    lb.querySelector('.prev').addEventListener('click', function () { go(cur - 1); });
    lb.querySelector('.next').addEventListener('click', function () { go(cur + 1); });
    lb.querySelector('.lb-stage').addEventListener('click', function (ev) { if (ev.target === this) close(); });
    document.addEventListener('keydown', function (ev) {
      if (lb.hidden) return;
      if (ev.key === 'Escape') close();
      else if (ev.key === 'ArrowLeft') go(cur - 1);
      else if (ev.key === 'ArrowRight') go(cur + 1);
    });
    var x0 = null, y0 = null;
    lb.addEventListener('touchstart', function (ev) { x0 = ev.touches[0].clientX; y0 = ev.touches[0].clientY; }, { passive: true });
    lb.addEventListener('touchend', function (ev) {
      if (x0 === null) return;
      var dx = ev.changedTouches[0].clientX - x0, dy = ev.changedTouches[0].clientY - y0;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) go(cur + (dx < 0 ? 1 : -1));
      else if (dy > 90 && Math.abs(dy) > Math.abs(dx)) close();
      x0 = null;
    });
  }

  // Contents: always open on wide screens, collapsed on phones
  var det = document.querySelector('.toc details');
  if (det && window.matchMedia('(min-width: 861px)').matches) det.open = true;

  // Trip page: highlight current section in contents
  var links = document.querySelectorAll('.toc a');
  if (links.length && 'IntersectionObserver' in window) {
    var map = {};
    links.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (en) {
        if (en.isIntersecting) {
          links.forEach(function (a) { a.classList.remove('on'); });
          var a = map[en.target.id]; if (a) a.classList.add('on');
        }
      });
    }, { rootMargin: '0px 0px -70% 0px' });
    Object.keys(map).forEach(function (id) { var h = document.getElementById(id); if (h) io.observe(h); });
  }
})();
