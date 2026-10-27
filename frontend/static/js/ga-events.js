/* GA4 click events. Sends only after analytics consent, the same gate as page_view. */
(function (root) {
    function readConsent() {
        var match = root.document && root.document.cookie
            ? root.document.cookie.match(/(?:^|; )cookie_consent=([^;]*)/)
            : null;
        return match ? decodeURIComponent(match[1]) : "";
    }

    function shouldSendGa(hostname, consent, hasGtag) {
        if (hostname === "localhost" || hostname === "127.0.0.1") {
            return false;
        }
        return consent === "1" && !!hasGtag;
    }

    function hostKey(host) {
        return String(host || "").replace(/^www\./, "").toLowerCase();
    }

    function isDirectionsHref(href) {
        var value = String(href || "").toLowerCase();
        return value.indexOf("google.com/maps") !== -1
            || value.indexOf("maps.google.") !== -1
            || value.indexOf("maps.app.goo.gl") !== -1
            || value.indexOf("goo.gl/maps") !== -1
            || value.indexOf("openstreetmap.org/directions") !== -1
            || value.indexOf("/maps/dir") !== -1;
    }

    function isDirectionsText(text) {
        var value = String(text || "").replace(/\s+/g, " ").trim().toLowerCase();
        if (!value || value.length > 80) {
            return false;
        }
        return value.indexOf("οδηγίες") !== -1
            || value.indexOf("direction") !== -1
            || value === "route"
            || value.indexOf("route ") === 0
            || value.indexOf("anfahrt") !== -1;
    }

    function isMapHref(href) {
        var value = String(href || "").trim();
        if (!value || value.indexOf("tel:") === 0 || value.indexOf("mailto:") === 0) {
            return false;
        }
        var path = value;
        var hash = "";
        try {
            var url = new URL(value, "https://veriaguide.gr");
            path = url.pathname;
            hash = url.hash;
        } catch (error) {
            hash = value.indexOf("#") === -1 ? "" : value.slice(value.indexOf("#"));
        }
        return /#map\b/.test(hash) || /(^|\/)map\/?$/.test(path);
    }

    function isMapText(text) {
        var value = String(text || "").replace(/\s+/g, " ").trim().toLowerCase();
        if (!value || value.length > 80) {
            return false;
        }
        return value === "map"
            || value === "χάρτης"
            || value.indexOf("χάρτη") !== -1
            || value.indexOf("on map") !== -1
            || value.indexOf("on the map") !== -1
            || value.indexOf("karte") !== -1;
    }

    function isExternal(href, pageHost) {
        if (!href || href.charAt(0) === "#" || href.charAt(0) === "/") {
            return false;
        }
        try {
            var url = new URL(href, "https://" + (pageHost || "veriaguide.gr"));
            if (url.protocol !== "http:" && url.protocol !== "https:") {
                return false;
            }
            return hostKey(url.hostname) !== hostKey(pageHost);
        } catch (error) {
            return false;
        }
    }

    function attr(node, name) {
        if (!node || !node.getAttribute) {
            return "";
        }
        return node.getAttribute(name) || "";
    }

    function classifyGaClick(link, pageHost) {
        if (!link || !link.getAttribute) {
            return "";
        }
        var marker = attr(link, "data-ga");
        if (marker === "tickets") {
            return "click_tickets";
        }
        if (marker === "event_details") {
            return "click_event_details";
        }
        var href = String(link.getAttribute("href") || link.href || "").trim();
        var text = link.textContent || "";
        var className = link.className || "";
        var lower = href.toLowerCase();
        if (lower.indexOf("tel:") === 0) {
            return "click_phone";
        }
        if (lower.indexOf("mailto:") === 0) {
            return "click_email";
        }
        if (isDirectionsHref(href) || isDirectionsText(text)) {
            return "click_directions";
        }
        if (isMapHref(href) || className.indexOf("show-on-favorites-map") !== -1 || isMapText(text)) {
            return "click_map";
        }
        if (marker === "website") {
            return "click_website";
        }
        if (isExternal(href, pageHost || "veriaguide.gr")) {
            return "click_outbound";
        }
        return "";
    }

    function eventClickParams(link, body) {
        return {
            event_title: attr(link, "data-event-title"),
            event_slug: attr(link, "data-event-slug"),
            event_date: attr(link, "data-event-date"),
            lang: attr(body, "data-lang"),
            link_url: link.href || attr(link, "href"),
            placement: attr(link, "data-ga-placement")
        };
    }

    function listingClickParams(link, body) {
        return {
            listing_type: attr(body, "data-listing-type"),
            listing_slug: attr(body, "data-listing-slug"),
            listing_title: attr(body, "data-listing-title"),
            lang: attr(body, "data-lang"),
            link_url: link.href || attr(link, "href")
        };
    }

    function onClick(event) {
        var target = event.target;
        var link = target && target.closest ? target.closest("a, button") : null;
        if (!link || !root.gtag) {
            return;
        }
        if (!shouldSendGa(root.location.hostname, readConsent(), true)) {
            return;
        }
        var name = classifyGaClick(link, root.location.hostname);
        if (!name) {
            return;
        }
        var body = root.document && root.document.body;
        var params = (name === "click_tickets" || name === "click_event_details")
            ? eventClickParams(link, body)
            : listingClickParams(link, body);
        root.gtag("event", name, params);
    }

    root.vgClassifyGaClick = classifyGaClick;
    root.vgShouldSendGa = shouldSendGa;
    root.vgOnGaClick = onClick;
    if (root.document && root.document.addEventListener) {
        root.document.addEventListener("click", onClick);
    }
})(typeof globalThis !== "undefined" ? globalThis : this);
