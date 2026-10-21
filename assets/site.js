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
        y.querySelector('small').textContent = n + ' ' + plural(n, 'поездка', 'поездки', 'поездок');
      });
      count.textContent = shown + ' из ' + trips.length;
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
    var LV = '1.9.4', CDN = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/' + LV + '/';
    function loadCss(h) { var l = document.createElement('link'); l.rel = 'stylesheet'; l.href = h; document.head.appendChild(l); }
    function loadJs(src, cb) { var sc = document.createElement('script'); sc.src = src; sc.onload = function () { cb(); }; sc.onerror = function () { cb(new Error('load')); }; document.head.appendChild(sc); }
    function css(v) { return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }
    function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
    function build() {
      var box = document.getElementById('worldmap');
      var base = (document.querySelector('link[href*="assets/style.css"]').getAttribute('href') || '').replace(/style\.css.*$/, '');
      new Promise(function (ok, no) { if (window.__WM) return ok(); loadJs(base + 'map-data.js?v=' + (document.querySelector('script[src*="site.js"]').src.split('v=')[1] || ''), function (e) { e ? no(e) : ok(); }); }).then(function () {
        var d = [window.__WM.k, window.__WM.c];
        box.innerHTML = '';
        var dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        var map = L.map(box, { zoomSnap: 0.5, minZoom: 2, worldCopyJump: true, attributionControl: true, scrollWheelZoom: false });
        map.on('focus', function () { map.scrollWheelZoom.enable(); });
        map.on('blur', function () { map.scrollWheelZoom.disable(); });
        var esri = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_' + (dark ? 'Dark' : 'Light') + '_Gray_';
        L.tileLayer(esri + 'Base/MapServer/tile/{z}/{y}/{x}', { maxZoom: 16, attribution: 'Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap' }).addTo(map);
        map.createPane('labels'); map.getPane('labels').style.zIndex = 350; map.getPane('labels').style.pointerEvents = 'none';
        L.tileLayer(esri + 'Reference/MapServer/tile/{z}/{y}/{x}', { maxZoom: 16, pane: 'labels' }).addTo(map);
        var acc = css('--accent'), soft = css('--accent-soft'), muted = css('--muted'), surf = css('--surface');
        var countries = L.geoJSON(d[0], {
          style: { color: acc, weight: 1, opacity: .55, fillColor: acc, fillOpacity: dark ? .18 : .12 },
          onEachFeature: function (f, l) { l.bindTooltip(esc(f.properties.n), { sticky: true, className: 'wm-tip' }); }
        }).addTo(map);
        var pts = d[1].map(function (c) {
          var linked = !!c.s;
          var m = L.circleMarker([c.la, c.lo], { radius: linked ? 5 : 4, weight: linked ? 1.5 : 1.5, color: linked ? surf : muted, fillColor: linked ? acc : surf, fillOpacity: 1 });
          var h = '<div class="wm-pop"><b>' + esc(c.n) + '</b>' + (c.y ? '<span class="wm-y">' + esc(c.y) + '</span>' : '') +
            (linked ? '<a href="trips/' + esc(c.s) + '.html">' + esc(c.t) + ' →</a>' : '') + '</div>';
          m.bindPopup(h, { closeButton: false, className: 'wm-popup', offset: [0, -2] });
          m.bindTooltip(esc(c.n), { direction: 'top', offset: [0, -6], className: 'wm-tip' });
          return m;
        });
        var cities = L.featureGroup(pts).addTo(map);
        map.fitBounds(L.latLngBounds(d[1].filter(function (c) { return c.lo > -30; }).map(function (c) { return [c.la, c.lo]; })), { padding: [24, 24] });
      }).catch(function (er) { if (window.console) console.error(er); box.innerHTML = '<span class="maploading">Не удалось загрузить карту</span>'; });
    }
    function start() {
      if (wmDone) return; wmDone = true;
      if (window.L) return build();
      loadCss(CDN + 'leaflet.min.css');
      loadJs(CDN + 'leaflet.min.js', function (err) { if (err) { document.getElementById('worldmap').innerHTML = '<span class="maploading">Не удалось загрузить карту</span>'; return; } build(); });
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
      if (scroll && tabwrap && tabwrap.getBoundingClientRect().top < 47) {
        window.scrollTo(0, window.scrollY + tabwrap.getBoundingClientRect().top - 47);
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
