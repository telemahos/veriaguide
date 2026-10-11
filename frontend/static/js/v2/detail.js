/* VeriaGuide v2 detail pages: sticky in-page section nav with scroll-spy. */
(function () {
    'use strict';
    var nav = document.querySelector('[data-vg-sectionnav]');
    var sections = document.querySelectorAll('[data-vg-section]');
    if (!nav || sections.length < 2) { return; }
    var list = nav.querySelector('ul');
    var links = [];
    sections.forEach(function (sec) {
        var li = document.createElement('li');
        var a = document.createElement('a');
        a.href = '#' + sec.id;
        a.textContent = sec.dataset.title || sec.querySelector('h2').textContent;
        li.appendChild(a); list.appendChild(li); links.push(a);
    });
    nav.hidden = false;

    function setActive(id) {
        links.forEach(function (a) {
            var on = a.getAttribute('href') === '#' + id;
            if (on) { a.setAttribute('aria-current', 'true'); } else { a.removeAttribute('aria-current'); }
        });
    }
    if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) { if (e.isIntersecting) { setActive(e.target.id); } });
        }, { rootMargin: '-25% 0px -65% 0px' });
        sections.forEach(function (s) { io.observe(s); });
    }
})();
