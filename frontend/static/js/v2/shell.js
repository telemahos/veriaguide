/* VeriaGuide v2 shell: mobile menu, submenus (disclosure pattern), Escape/outside-click. */
(function () {
    'use strict';
    var header = document.querySelector('[data-vg-header]');
    if (!header) { return; }
    var toggle = header.querySelector('[data-vg-menu-toggle]');
    var nav = header.querySelector('[data-vg-nav]');
    var subToggles = header.querySelectorAll('[data-vg-sub-toggle]');

    function setMenu(open) {
        if (!toggle || !nav) { return; }
        toggle.setAttribute('aria-expanded', String(open));
        nav.classList.toggle('is-open', open);
    }
    function closeSubs(except) {
        subToggles.forEach(function (btn) {
            if (btn !== except) { btn.setAttribute('aria-expanded', 'false'); }
        });
    }

    if (toggle) {
        toggle.addEventListener('click', function () {
            setMenu(toggle.getAttribute('aria-expanded') !== 'true');
        });
    }
    subToggles.forEach(function (btn) {
        btn.addEventListener('click', function () {
            var open = btn.getAttribute('aria-expanded') !== 'true';
            closeSubs(btn);
            btn.setAttribute('aria-expanded', String(open));
        });
    });
    document.addEventListener('click', function (e) {
        if (!header.contains(e.target)) { closeSubs(); setMenu(false); }
    });
    document.addEventListener('keydown', function (e) {
        if (e.key !== 'Escape') { return; }
        var openSub = header.querySelector('[data-vg-sub-toggle][aria-expanded="true"]');
        closeSubs();
        setMenu(false);
        if (openSub) { openSub.focus(); } else if (toggle && toggle.offsetParent !== null) { toggle.focus(); }
    });

    // Mark the current section
    var path = location.pathname.replace(/\/$/, '') || '/';
    header.querySelectorAll('.vg-nav__link[href], .vg-subnav a').forEach(function (a) {
        var p = a.getAttribute('href');
        if (p && p.split('?')[0].replace(/\/$/, '') === path && path !== '/') {
            a.setAttribute('aria-current', 'page');
        }
    });
})();
