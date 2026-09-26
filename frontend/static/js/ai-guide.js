(function () {
    "use strict";

    var iso = function (d) {
        var tz = d.getTimezoneOffset() * 60000;
        return new Date(d.getTime() - tz).toISOString().slice(0, 10);
    };
    var parse = function (value) {
        return value ? new Date(value + "T00:00:00") : null;
    };

    function initDates(form) {
        var start = form.querySelector("[data-ag-start]");
        var end = form.querySelector("[data-ag-end]");
        var count = form.querySelector("[data-ag-count]");
        if (!start || !end) return;

        function update() {
            if (start.value) end.min = start.value;
            var a = parse(start.value), b = parse(end.value);
            if (!count) return;
            count.classList.remove("is-error");
            if (!a || !b || b < a) { count.textContent = ""; return; }
            var days = Math.round((b - a) / 86400000) + 1;
            if (days > 7) {
                count.textContent = count.dataset.tooLong;
                count.classList.add("is-error");
                return;
            }
            count.textContent = days + " " + (days === 1 ? count.dataset.day : count.dataset.days);
        }

        start.addEventListener("change", function () {
            if (!end.value || parse(end.value) < parse(start.value)) end.value = start.value;
            update();
        });
        end.addEventListener("change", update);

        form.querySelectorAll("[data-ag-preset]").forEach(function (chip) {
            chip.addEventListener("click", function () {
                var today = new Date();
                today.setHours(0, 0, 0, 0);
                var preset = chip.dataset.agPreset;
                var a = new Date(today), b;
                if (preset === "weekend") {
                    var toSat = (6 - a.getDay() + 7) % 7;
                    a.setDate(a.getDate() + toSat);
                    b = new Date(a);
                    b.setDate(b.getDate() + 1);
                } else {
                    a.setDate(a.getDate() + 1);
                    b = new Date(a);
                    b.setDate(b.getDate() + parseInt(preset, 10) - 1);
                }
                start.value = iso(a);
                end.value = iso(b);
                form.querySelectorAll("[data-ag-preset]").forEach(function (c) { c.classList.toggle("is-active", c === chip); });
                update();
            });
        });
        update();
    }

    function initInterests(form) {
        var hint = form.querySelector("[data-ag-selected]");
        if (!hint) return;
        var boxes = form.querySelectorAll('input[name="interests"]');
        function update() {
            var n = Array.prototype.filter.call(boxes, function (b) { return b.checked; }).length;
            hint.textContent = n ? n + " " + hint.dataset.some : hint.dataset.none;
        }
        boxes.forEach(function (b) { b.addEventListener("change", update); });
        update();
    }

    function initAutoNext(form) {
        var pointer = false;
        form.addEventListener("pointerdown", function () { pointer = true; });
        form.addEventListener("keydown", function () { pointer = false; });
        form.querySelectorAll("[data-ag-autonext]").forEach(function (input) {
            input.addEventListener("change", function () {
                if (!pointer) return;
                window.setTimeout(function () {
                    if (form.requestSubmit) form.requestSubmit(); else form.submit();
                }, 260);
            });
        });
    }

    function initWishes(form) {
        var area = form.querySelector("[data-ag-wishes]");
        var chars = form.querySelector("[data-ag-chars]");
        if (!area) return;
        function update() {
            if (chars) chars.textContent = area.value.length;
        }
        area.addEventListener("input", update);
        function parts() {
            return area.value.split(",").map(function (part) { return part.trim(); }).filter(Boolean);
        }
        function syncChips() {
            var chosen = parts();
            form.querySelectorAll("[data-ag-suggest]").forEach(function (chip) {
                chip.classList.toggle("is-active", chosen.indexOf(chip.dataset.agSuggest) !== -1);
            });
        }
        form.querySelectorAll("[data-ag-suggest]").forEach(function (chip) {
            chip.addEventListener("click", function () {
                var text = chip.dataset.agSuggest;
                var chosen = parts();
                var index = chosen.indexOf(text);
                if (index === -1) chosen.push(text);
                else chosen.splice(index, 1);
                var next = chosen.join(", ");
                if (next.length > 500) return;
                area.value = next;
                syncChips();
                update();
                area.focus();
            });
        });
        area.addEventListener("input", syncChips);
        syncChips();
        update();
    }

    function initGenerate() {
        var overlay = document.querySelector("[data-ag-loading]");
        document.querySelectorAll("[data-ag-generate]").forEach(function (form) {
            form.addEventListener("submit", function () {
                if (!overlay) return;
                overlay.hidden = false;
                var steps = overlay.querySelectorAll(".ag-loading__steps li");
                var i = 0;
                if (steps[0]) steps[0].classList.add("is-active");
                window.setInterval(function () {
                    if (i >= steps.length - 1) return;
                    steps[i].classList.remove("is-active");
                    steps[i].classList.add("is-done");
                    i += 1;
                    steps[i].classList.add("is-active");
                }, 4500);
                form.querySelectorAll('button[type="submit"]').forEach(function (b) { b.disabled = true; });
            });
        });
        window.addEventListener("pageshow", function (e) {
            if (e.persisted && overlay) overlay.hidden = true;
        });
    }

    function initResult() {
        var print = document.querySelector("[data-ag-print]");
        if (print) print.addEventListener("click", function () { window.print(); });

        var share = document.querySelector("[data-ag-share]");
        if (share) {
            share.addEventListener("click", function () {
                var label = share.querySelector("span");
                var done = function () {
                    var prev = label.textContent;
                    label.textContent = share.dataset.copied;
                    window.setTimeout(function () { label.textContent = prev; }, 2000);
                };
                if (navigator.share) {
                    navigator.share({ title: document.title, url: location.href }).catch(function () {});
                } else if (navigator.clipboard) {
                    navigator.clipboard.writeText(location.href).then(done);
                }
            });
        }

        var links = document.querySelectorAll(".ag-daynav__item");
        if (!links.length || !("IntersectionObserver" in window)) return;
        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                links.forEach(function (l) { l.classList.toggle("is-active", l.getAttribute("href") === "#" + entry.target.id); });
            });
        }, { rootMargin: "-40% 0px -55% 0px" });
        document.querySelectorAll(".ag-day").forEach(function (d) { observer.observe(d); });
    }

    document.querySelectorAll("[data-ag-step]").forEach(function (form) {
        initDates(form);
        initInterests(form);
        initAutoNext(form);
        initWishes(form);
    });
    function initRouteMap() {
        var el = document.getElementById("ag-route-map");
        var dataEl = document.getElementById("ag-route-data");
        if (!el || !dataEl) return;
        if (typeof L === "undefined" || typeof VeriaGuideMaps === "undefined") {
            window.setTimeout(initRouteMap, 80);
            return;
        }
        var route;
        try { route = JSON.parse(dataEl.textContent || "{}"); } catch (e) { return; }
        var map = L.map(el, { scrollWheelZoom: false });
        VeriaGuideMaps.addBaseLayer(map);
        var bounds = [];
        (route.days || []).forEach(function (day) {
            (day.stops || []).forEach(function (stop) { bounds.push([stop.lat, stop.lng]); });
            (day.line || []).forEach(function (point) { bounds.push(point); });
            if ((day.line || []).length > 1) {
                L.polyline(day.line, { color: day.color || "#c8863a", weight: 5, opacity: 0.9 }).addTo(map);
            }
            (day.stops || []).forEach(function (stop) {
                var icon = L.divIcon({
                    className: "",
                    html: '<span class="ag-stop-pin" style="background:' + (day.color || "#c8863a") + '">' + stop.n + "</span>",
                    iconSize: [28, 28],
                    iconAnchor: [14, 14]
                });
                L.marker([stop.lat, stop.lng], { icon: icon }).bindPopup("<strong>" + stop.n + ". " + stop.name + "</strong>").addTo(map);
            });
        });
        function showAll() {
            map.invalidateSize({ animate: false });
            if (bounds.length) {
                var frame = L.latLngBounds(bounds);
                var span = Math.max(frame.getEast() - frame.getWest(), 0.04);
                frame.extend([frame.getNorth(), frame.getEast() + span * 0.45]);
                map.fitBounds(frame, {
                    paddingTopLeft: [28, 28],
                    paddingBottomRight: [28, 28],
                    maxZoom: 12,
                    animate: false
                });
            }
            else map.setView([40.52, 22.2], 13);
        }
        showAll();
        window.setTimeout(showAll, 200);
        window.addEventListener("beforeprint", showAll);
    }

    initGenerate();
    initResult();
    initRouteMap();
})();
