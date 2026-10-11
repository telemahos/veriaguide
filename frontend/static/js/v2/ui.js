/* VeriaGuide v2 ui: tiny replacement for the Bootstrap behaviours still used by shared markup
   (data-bs-toggle="modal|collapse", data-bs-dismiss="modal", data-bs-slide). No dependencies. */
(function () {
    'use strict';
    var openModal = null, backdrop = null, lastFocus = null;

    function sel(el) {
        var t = el.getAttribute('data-bs-target') || el.getAttribute('href');
        return t && t.charAt(0) === '#' ? document.querySelector(t) : null;
    }
    function fire(el, name) { el.dispatchEvent(new CustomEvent(name, { bubbles: true })); }

    function showModal(m) {
        if (!m || openModal === m) { return; }
        if (openModal) { hideModal(); }
        lastFocus = document.activeElement;
        fire(m, 'show.bs.modal');
        backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop';
        document.body.appendChild(backdrop);
        m.style.display = 'block';
        m.removeAttribute('aria-hidden');
        m.setAttribute('aria-modal', 'true');
        m.setAttribute('role', 'dialog');
        void m.offsetWidth;
        m.classList.add('show');
        document.body.style.overflow = 'hidden';
        openModal = m;
        var f = m.querySelector('[data-bs-dismiss], button, [href], input, select, textarea');
        if (f) { f.focus(); }
        fire(m, 'shown.bs.modal');
    }
    function hideModal() {
        var m = openModal;
        if (!m) { return; }
        fire(m, 'hide.bs.modal');
        m.classList.remove('show');
        m.style.display = '';
        m.setAttribute('aria-hidden', 'true');
        m.removeAttribute('aria-modal');
        if (backdrop) { backdrop.remove(); backdrop = null; }
        document.body.style.overflow = '';
        openModal = null;
        if (lastFocus && lastFocus.focus) { lastFocus.focus(); }
        fire(m, 'hidden.bs.modal');
    }

    function toggleCollapse(trigger, panel) {
        if (!panel) { return; }
        var open = !panel.classList.contains('show');
        var parentSel = panel.getAttribute('data-bs-parent');
        if (open && parentSel) {
            var parent = document.querySelector(parentSel);
            if (parent) {
                parent.querySelectorAll('.collapse.show').forEach(function (p) {
                    if (p === panel) { return; }
                    p.classList.remove('show');
                    parent.querySelectorAll('[data-bs-target="#' + p.id + '"], [href="#' + p.id + '"]').forEach(function (b) {
                        b.classList.add('collapsed'); b.setAttribute('aria-expanded', 'false');
                    });
                });
            }
        }
        panel.classList.toggle('show', open);
        document.querySelectorAll('[data-bs-target="#' + panel.id + '"], [href="#' + panel.id + '"]').forEach(function (b) {
            b.classList.toggle('collapsed', !open); b.setAttribute('aria-expanded', String(open));
        });
    }

    function slide(carousel, dir) {
        var items = carousel.querySelectorAll('.carousel-item');
        if (!items.length) { return; }
        var i = Array.prototype.findIndex.call(items, function (n) { return n.classList.contains('active'); });
        items[Math.max(i, 0)].classList.remove('active');
        items[(Math.max(i, 0) + dir + items.length) % items.length].classList.add('active');
    }

    document.addEventListener('click', function (e) {
        var t = e.target.closest('[data-bs-toggle], [data-bs-dismiss], [data-bs-slide]');
        if (t) {
            var kind = t.getAttribute('data-bs-toggle');
            if (kind === 'modal') { e.preventDefault(); showModal(sel(t)); return; }
            if (kind === 'collapse') { e.preventDefault(); toggleCollapse(t, sel(t)); return; }
            if (t.getAttribute('data-bs-dismiss') === 'modal') { e.preventDefault(); hideModal(); return; }
            var dir = t.getAttribute('data-bs-slide');
            if (dir) { e.preventDefault(); var c = sel(t); if (c) { slide(c, dir === 'prev' ? -1 : 1); } return; }
        }
        if (openModal && e.target === openModal) { hideModal(); }
    });
    document.addEventListener('keydown', function (e) {
        if (!openModal) { return; }
        if (e.key === 'Escape') { hideModal(); return; }
        if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
            var c = openModal.querySelector('.carousel');
            if (c) { slide(c, e.key === 'ArrowLeft' ? -1 : 1); }
        }
        if (e.key === 'Tab') {
            var f = openModal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (!f.length) { return; }
            var first = f[0], last = f[f.length - 1];
            if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
            else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
        }
    });
})();
