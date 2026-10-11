/* VeriaGuide v2 search: accessible combobox on top of /api/search/autocomplete. */
(function () {
    'use strict';
    var lang = document.documentElement.lang || 'en';
    var prefix = lang === 'el' ? '/el' : (lang === 'de' ? '/de' : '');

    document.querySelectorAll('[data-vg-search]').forEach(function (form) {
        var input = form.querySelector('input[name="q"]');
        var list = form.querySelector('.vg-suggest');
        var status = form.querySelector('[data-vg-search-status]');
        if (!input || !list) { return; }
        var timer, controller, active = -1;

        function close() {
            list.hidden = true; list.innerHTML = ''; active = -1;
            input.setAttribute('aria-expanded', 'false');
            input.removeAttribute('aria-activedescendant');
        }
        function setActive(i) {
            var opts = list.querySelectorAll('[role="option"]');
            if (!opts.length) { return; }
            if (opts[active]) { opts[active].removeAttribute('aria-selected'); }
            active = (i + opts.length) % opts.length;
            opts[active].setAttribute('aria-selected', 'true');
            input.setAttribute('aria-activedescendant', opts[active].id);
            opts[active].scrollIntoView({ block: 'nearest' });
        }
        function skeleton() {
            list.hidden = false;
            list.innerHTML = '<li class="vg-suggest__skel" aria-hidden="true"><span class="skeleton"></span></li>'.repeat(3);
            input.setAttribute('aria-expanded', 'true');
        }
        function render(items) {
            items = (items || []).filter(function (it) { return it.slug && it.slug !== 'null'; });
            list.innerHTML = '';
            if (!items.length) {
                var empty = document.createElement('li');
                empty.className = 'vg-suggest__empty';
                empty.textContent = list.dataset.noResults || '';
                list.appendChild(empty);
                if (status) { status.textContent = list.dataset.noResults || ''; }
                return;
            }
            items.forEach(function (it, i) {
                var li = document.createElement('li');
                li.setAttribute('role', 'option');
                li.id = input.id + '-opt-' + i;
                var a = document.createElement('a');
                a.href = prefix + '/' + it.category + '/' + it.slug;
                a.tabIndex = -1;
                if (it.image) {
                    var img = document.createElement('img');
                    img.src = it.image; img.alt = ''; img.width = 44; img.height = 44; img.loading = 'lazy';
                    a.appendChild(img);
                } else {
                    var ph = document.createElement('span');
                    ph.className = 'vg-suggest__ph'; ph.setAttribute('aria-hidden', 'true');
                    a.appendChild(ph);
                }
                var t = document.createElement('span');
                var strong = document.createElement('strong'); strong.textContent = it.title;
                var small = document.createElement('small'); small.textContent = it.category_label || '';
                t.appendChild(strong); t.appendChild(small); a.appendChild(t);
                li.appendChild(a); list.appendChild(li);
            });
            if (status) { status.textContent = items.length + ' ' + (list.dataset.resultsLabel || ''); }
        }

        input.addEventListener('input', function () {
            clearTimeout(timer);
            var q = input.value.trim();
            if (q.length < 2) { close(); return; }
            timer = setTimeout(function () {
                if (controller) { controller.abort(); }
                controller = new AbortController();
                skeleton();
                fetch('/api/search/autocomplete?q=' + encodeURIComponent(q) + '&lang=' + encodeURIComponent(lang), { signal: controller.signal })
                    .then(function (r) { if (!r.ok) { throw new Error(r.status); } return r.json(); })
                    .then(function (data) { render(data); active = -1; })
                    .catch(function (e) { if (e.name !== 'AbortError') { close(); } });
            }, 250);
        });
        input.addEventListener('keydown', function (e) {
            if (list.hidden) { return; }
            if (e.key === 'ArrowDown') { e.preventDefault(); setActive(active + 1); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(active - 1); }
            else if (e.key === 'Escape') { close(); }
            else if (e.key === 'Enter' && active >= 0) {
                var a = list.querySelectorAll('[role="option"] a')[active];
                if (a) { e.preventDefault(); location.href = a.href; }
            }
        });
        document.addEventListener('click', function (e) { if (!form.contains(e.target)) { close(); } });
        form.addEventListener('focusout', function () {
            setTimeout(function () { if (!form.contains(document.activeElement)) { close(); } }, 0);
        });
    });
})();
