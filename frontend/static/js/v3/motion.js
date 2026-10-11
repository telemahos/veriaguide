/* VeriaGuide v3 "Zeitalter": scroll reveals, parallax, overlay header, dark/light switch.
   The inline head script sets <html data-scheme> and adds .zt-motion unless the user prefers reduced motion. */
(function () {
    'use strict';
    var root = document.documentElement;

    /* ---- Dark / light switch (works with or without motion) ---- */
    function setScheme(next) {
        root.setAttribute('data-scheme', next);
        try { localStorage.setItem('vg_scheme', next); } catch (e) { /* private mode */ }
        document.querySelectorAll('[data-zt-scheme]').forEach(function (btn) {
            var light = next === 'light';
            btn.setAttribute('aria-pressed', String(light));
            btn.setAttribute('aria-label', light ? btn.dataset.labelDark : btn.dataset.labelLight);
        });
    }
    document.querySelectorAll('[data-zt-scheme]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            setScheme(root.getAttribute('data-scheme') === 'light' ? 'dark' : 'light');
        });
    });
    setScheme(root.getAttribute('data-scheme') === 'light' ? 'light' : 'dark');

    /* ---- Header search (works with or without motion) ---- */
    var searchBtn = document.querySelector('[data-zt-search-toggle]');
    var searchBar = document.getElementById('zt-search');
    function setSearch(open) {
        if (!searchBtn || !searchBar) { return; }
        searchBar.hidden = !open;
        searchBtn.setAttribute('aria-expanded', String(open));
        if (open) {
            var input = searchBar.querySelector('input[type="search"]');
            if (input) { input.focus(); }
        }
    }
    if (searchBtn && searchBar) {
        searchBtn.addEventListener('click', function () { setSearch(searchBar.hidden); });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && !searchBar.hidden) { setSearch(false); searchBtn.focus(); }
            else if (e.key === '/' && searchBar.hidden && !/^(input|textarea|select)$/i.test((document.activeElement || {}).tagName || '')) {
                e.preventDefault(); setSearch(true);
            }
        });
        document.addEventListener('click', function (e) {
            if (!searchBar.hidden && !searchBar.contains(e.target) && !searchBtn.contains(e.target)) { setSearch(false); }
        });
    }

    /* ---- Header over the hero: solid once the page scrolls ---- */
    var overlay = document.querySelector('[data-zt-overlay]');
    function onScrollHeader() {
        if (overlay) { overlay.classList.toggle('is-scrolled', window.scrollY > 40); }
    }

    if (!root.classList.contains('zt-motion')) {
        window.addEventListener('scroll', onScrollHeader, { passive: true });
        onScrollHeader();
        return;
    }

    /* ---- Reveal on scroll ---- */
    var vh = window.innerHeight;
    var auto = '.vg-card, .vg-tile, .vg-section-head, .vg-pagehead__intro, .vg-empty, .vg-chips, ' +
        '.detail-content-section, .detail-sidebar-card, .detail-page .card, .detail-trust-box, ' +
        '.vg-filters__panel, .vg-pagination, .ag-feature, .ag-hero__copy';
    document.querySelectorAll(auto).forEach(function (el) {
        if (el.hasAttribute('data-reveal') || el.closest('[data-reveal]')) { return; }
        if (el.getBoundingClientRect().top < vh * 0.92) { return; } /* already visible: never hide it */
        el.setAttribute('data-reveal', '');
    });

    /* stagger siblings that enter together */
    var groups = new Map();
    document.querySelectorAll('[data-reveal]').forEach(function (el) {
        var parent = el.parentElement;
        var i = groups.get(parent) || 0;
        if (!el.style.getPropertyValue('--zt-delay')) { el.style.setProperty('--zt-delay', (Math.min(i, 5) * 0.09) + 's'); }
        groups.set(parent, i + 1);
    });

    var targets = document.querySelectorAll('[data-reveal]');
    if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-in');
                    io.unobserve(entry.target);
                }
            });
        }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
        targets.forEach(function (el) { io.observe(el); });
    } else {
        targets.forEach(function (el) { el.classList.add('is-in'); });
    }
    root.classList.add('zt-motion-ready');

    /* ---- Parallax ---- */
    var layers = Array.prototype.slice.call(document.querySelectorAll('[data-parallax]'));
    var ticking = false;
    function update() {
        ticking = false;
        vh = window.innerHeight;
        layers.forEach(function (el) {
            var box = el.parentElement.getBoundingClientRect();
            if (box.bottom < -200 || box.top > vh + 200) { return; }
            var factor = parseFloat(el.getAttribute('data-parallax')) || 0.12;
            var offset = (box.top + box.height / 2 - vh / 2) * -factor;
            el.style.transform = 'translate3d(0,' + offset.toFixed(1) + 'px,0)';
        });
        onScrollHeader();
    }
    function request() {
        if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
    }
    window.addEventListener('scroll', request, { passive: true });
    window.addEventListener('resize', request);
    update();
})();
