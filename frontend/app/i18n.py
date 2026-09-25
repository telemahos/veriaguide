"""Greek UI translations and /el/ path handling.

English stays on the existing URLs. Greek pages live under /el/ and reuse the
same templates. Post content is not translated here: title_el, excerpt_el and
content_el come from WordPress and are applied in the API layer.
"""
import contextvars
import re

from jinja2 import pass_context

_lang: contextvars.ContextVar[str] = contextvars.ContextVar("vg_lang", default="en")

SUPPORTED = ("en", "el")

# Internal paths that must not pick up the /el prefix.
_UNPREFIXED = ("/static/", "/api/", "/admin", "/health", "/sitemap", "/robots", "/wp-", "/favicon")


def current_lang() -> str:
    return _lang.get()


def set_lang(lang: str):
    return _lang.set(lang if lang in SUPPORTED else "en")


def reset_lang(token) -> None:
    _lang.reset(token)


def tr(text: str | None, lang: str | None = None) -> str:
    """Translate a UI string when the active language is Greek."""
    if text is None:
        return ""
    text = str(text)
    if (lang or current_lang()) != "el" or not text.strip():
        return text
    key = " ".join(text.split())
    return UI_EL.get(key, text)


@pass_context
def translate(context, text: str | None) -> str:
    """Jinja filter. Uses the template language, not a thread-local value."""
    lang = "en"
    if context is not None:
        lang = context.get("lang") or current_lang()
    return tr(text, lang)


def localized_path(path: str, lang: str | None = None) -> str:
    """Return the public path for a language. `path` may already contain /el."""
    lang = lang or current_lang()
    if not path:
        path = "/"
    if not path.startswith("/"):
        path = "/" + path
    bare = path[3:] if path == "/el" or path.startswith("/el/") else path
    if not bare.startswith("/"):
        bare = "/" + bare
    if lang != "el":
        return bare or "/"
    if bare == "/":
        return "/el/"
    return "/el" + bare


def absolute_url(path: str, lang: str, query: str = "") -> str:
    from app.config import SITE_URL

    url = f"{SITE_URL.rstrip('/')}{localized_path(path, lang)}"
    if query:
        url = f"{url}?{query}"
    return url


def language_switch_urls(path: str, query: str = "") -> dict[str, str]:
    return {lang: absolute_url(path, lang, query) for lang in SUPPORTED}


def _should_prefix(url: str) -> bool:
    path = url.split("?", 1)[0].split("#", 1)[0]
    if path == "/el" or path.startswith("/el/"):
        return False
    return not any(path == item.rstrip("/") or path.startswith(item) for item in _UNPREFIXED)


def localize_href(url: str) -> str:
    """Prefix a menu or content link when the current page is Greek."""
    if current_lang() != "el" or not url or url == "#":
        return url
    from app.config import SITE_URL

    base = SITE_URL.rstrip("/")
    if url.startswith(base):
        return absolute_url(url[len(base):] or "/", "el")
    if url.startswith("/") and _should_prefix(url):
        return "/el/" if url == "/" else "/el" + url
    return url


def prefix_internal_links(html: str) -> str:
    """Prefix same-site href/action paths with /el on Greek pages."""

    def repl(match: re.Match) -> str:
        attr, quote, url = match.group(1), match.group(2), match.group(3)
        if not _should_prefix(url):
            return match.group(0)
        if url == "/":
            prefixed = "/el/"
        else:
            prefixed = "/el" + url
        return f"{attr}={quote}{prefixed}{quote}"

    return re.sub(r"\b(href|action)=([\"'])(/[^\"']*)\2", repl, html)


def localize_post(post: dict) -> dict:
    """Overlay Greek title, excerpt and content stored as post meta."""
    if current_lang() != "el" or not isinstance(post, dict):
        return post
    meta = post.get("meta")
    if not isinstance(meta, dict):
        return post

    fields = (("title", "title_el"), ("excerpt", "excerpt_el"), ("content", "content_el"))
    if not any(isinstance(meta.get(key), str) and meta.get(key).strip() for _, key in fields):
        return post

    localized = dict(post)
    for field, key in fields:
        value = meta.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        block = dict(localized.get(field) or {})
        block["rendered"] = value
        localized[field] = block
    return localized


def localize_posts(posts):
    if current_lang() != "el" or not isinstance(posts, list):
        return posts
    return [localize_post(post) if isinstance(post, dict) else post for post in posts]


UI_EL: dict[str, str] = {
    "Language": "Γλώσσα",
    "Home": "Αρχική",
    "Destinations": "Προορισμοί",
    "Food & Drink": "Φαγητό και ποτό",
    "Favorites": "Αγαπημένα",
    "Email us": "Στείλτε μας email",
    "Toggle navigation": "Μενού",
    "Explore": "Εξερευνήστε",
    "Info": "Πληροφορίες",
    "Get Involved": "Συμμετοχή",
    "Contact": "Επικοινωνία",
    "Contact Us": "Επικοινωνία",
    "About Us": "Σχετικά με εμάς",
    "About VeriaGuide": "Σχετικά με το VeriaGuide",
    "Sitemap": "Χάρτης ιστοτόπου",
    "Add Your Business": "Καταχωρίστε την επιχείρησή σας",
    "Share Your Experience": "Μοιραστείτε την εμπειρία σας",
    "Search": "Αναζήτηση",
    "Search Veria": "Αναζήτηση στη Βέροια",
    "Search VeriaGuide": "Αναζήτηση στο VeriaGuide",
    "Browse categories": "Κατηγορίες",
    "Explore categories": "Εξερευνήστε κατηγορίες",
    "Churches": "Ναοί",
    "Museums": "Μουσεία",
    "Archaeological Sites": "Αρχαιολογικοί χώροι",
    "Archaeological sites": "Αρχαιολογικοί χώροι",
    "Religious Sites": "Θρησκευτικοί χώροι",
    "Ski Resorts": "Χιονοδρομικά κέντρα",
    "Tours": "Περιηγήσεις",
    "Hiking Trails": "Μονοπάτια",
    "Hidden Gems": "Κρυμμένοι θησαυροί",
    "Restaurants": "Εστιατόρια",
    "Cafés": "Καφέ",
    "Accommodations": "Διαμονή",
    "Interactive Map": "Διαδραστικός χάρτης",
    "Interactive map": "Διαδραστικός χάρτης",
    "Map": "Χάρτης",
    "Churches & Monasteries": "Ναοί και μοναστήρια",
    "Your ultimate guide to exploring Veria, Greece. Discover Byzantine churches, ancient ruins, traditional cuisine, and mountain adventures.": "Ο οδηγός σας για τη Βέροια. Ανακαλύψτε βυζαντινούς ναούς, αρχαία ερείπια, τοπική κουζίνα και βουνά.",
    "Veria (Veroia), Imathia, Greece": "Βέροια, Ημαθία, Ελλάδα",
    "Veria, Imathia, Greece": "Βέροια, Ημαθία, Ελλάδα",
    "VeriaGuide – All rights reserved": "VeriaGuide – Με την επιφύλαξη παντός δικαιώματος",
    "Welcome to Veria, Imathia": "Καλώς ήρθατε στη Βέροια",
    "Discover Veria (Veroia) — the heart of Macedonia": "Ανακαλύψτε τη Βέροια — την καρδιά της Μακεδονίας",
    "Byzantine churches and historic streets in Veria, Imathia, Greece": "Βυζαντινοί ναοί και ιστορικοί δρόμοι στη Βέροια Ημαθίας",
    "View all": "Όλα",
    "View all accommodations": "Όλα τα καταλύματα",
    "View all archaeological sites": "Όλοι οι αρχαιολογικοί χώροι",
    "View all cafes": "Όλα τα καφέ",
    "View all hidden gems": "Όλοι οι κρυμμένοι θησαυροί",
    "View all hiking trails": "Όλα τα μονοπάτια",
    "View all museums": "Όλα τα μουσεία",
    "View all religious sites": "Όλοι οι θρησκευτικοί χώροι",
    "View all restaurants": "Όλα τα εστιατόρια",
    "View all ski_resorts": "Όλα τα χιονοδρομικά",
    "View all tours": "Όλες οι περιηγήσεις",
    "View Details": "Λεπτομέρειες",
    "View details": "Λεπτομέρειες",
    "View Menu": "Μενού",
    "View Tour": "Προβολή περιήγησης",
    "View Trail": "Προβολή μονοπατιού",
    "View on Map": "Προβολή στον χάρτη",
    "Show on map": "Εμφάνιση στον χάρτη",
    "More Info": "Περισσότερα",
    "More in Veria": "Περισσότερα στη Βέροια",
    "Discover More": "Ανακαλύψτε περισσότερα",
    "Get Directions": "Οδηγίες",
    "Get Directions to Trailhead": "Οδηγίες για την αφετηρία",
    "Call Now": "Καλέστε τώρα",
    "Book Now": "Κράτηση",
    "Book Now (Coming Soon)": "Κράτηση (σύντομα)",
    "Visit Website": "Ιστότοπος",
    "Add to Favorites": "Προσθήκη στα αγαπημένα",
    "Add to favorites": "Προσθήκη στα αγαπημένα",
    "My Favorites": "Τα αγαπημένα μου",
    "Your saved favorite places in Veria": "Τα μέρη που αποθηκεύσατε στη Βέροια",
    "You haven't added any favorites yet": "Δεν έχετε προσθέσει ακόμη αγαπημένα",
    "Explore Veria and add places you like to your favorites!": "Εξερευνήστε τη Βέροια και αποθηκεύστε όσα μέρη σας αρέσουν.",
    "Search in your favorites": "Αναζήτηση στα αγαπημένα",
    "Clear All": "Εκκαθάριση όλων",
    "Clear All Filters": "Εκκαθάριση φίλτρων",
    "Clear Search": "Εκκαθάριση αναζήτησης",
    "Clear filter": "Καθαρισμός φίλτρου",
    "Close": "Κλείσιμο",
    "Next": "Επόμενο",
    "Previous": "Προηγούμενο",
    "Back to Home": "Πίσω στην αρχική",
    "Go Back": "Πίσω",
    "Search again": "Νέα αναζήτηση",
    "No Results Found": "Δεν βρέθηκαν αποτελέσματα",
    "Try adjusting your search or category to find what you're looking for.": "Δοκιμάστε άλλη αναζήτηση ή κατηγορία.",
    "Try adjusting your search terms": "Δοκιμάστε άλλους όρους",
    "Try different keywords": "Δοκιμάστε διαφορετικές λέξεις",
    "Try these popular searches:": "Δημοφιλείς αναζητήσεις:",
    "Use more general terms": "Χρησιμοποιήστε γενικότερους όρους",
    "Check your spelling": "Ελέγξτε την ορθογραφία",
    "Search Tips:": "Συμβουλές αναζήτησης:",
    "Search Results": "Αποτελέσματα",
    "Popular Searches:": "Δημοφιλείς αναζητήσεις:",
    "Popular Pages:": "Δημοφιλείς σελίδες:",
    "Page Not Found": "Η σελίδα δεν βρέθηκε",
    "Page Not Found - VeriaGuide": "Η σελίδα δεν βρέθηκε - VeriaGuide",
    "The page you're looking for doesn't exist. Maybe you took a wrong turn?": "Η σελίδα που ψάχνετε δεν υπάρχει. Μήπως πήρατε λάθος στροφή;",
    "Internal Server Error": "Εσωτερικό σφάλμα",
    "Server Error - VeriaGuide": "Σφάλμα διακομιστή - VeriaGuide",
    "An unexpected error occurred. Our team has been notified and is working on a fix.": "Παρουσιάστηκε απρόσμενο σφάλμα. Το ενημερωθήκαμε και το διορθώνουμε.",
    "Error": "Σφάλμα",
    "Too Many Requests": "Πάρα πολλά αιτήματα",
    "Too Many Requests - VeriaGuide": "Πάρα πολλά αιτήματα - VeriaGuide",
    "You've sent too many requests in a short time. Please wait a moment.": "Στείλατε πολλά αιτήματα σε λίγο χρόνο. Περιμένετε λίγο.",
    "Why am I seeing this?": "Γιατί το βλέπω αυτό;",
    "To protect our servers and provide fast service to all users, we limit the number of requests per minute. Please try again shortly.": "Για να μένει ο ιστότοπος γρήγορος για όλους, περιορίζουμε τα αιτήματα ανά λεπτό. Δοκιμάστε ξανά σε λίγο.",
    "Please provide this ID if you contact support.": "Αναφέρετε αυτόν τον κωδικό αν επικοινωνήσετε με την υποστήριξη.",
    "Go to slide": "Μετάβαση στη διαφάνεια",
    "Show photo": "Προβολή φωτογραφίας",
    "Please enter at least 2 characters to search.": "Πληκτρολογήστε τουλάχιστον 2 χαρακτήρες.",
    "Open photo gallery": "Άνοιγμα συλλογής φωτογραφιών",
    "Gallery thumbnails": "Μικρογραφίες",
    "No photo available": "Δεν υπάρχει φωτογραφία",
    "Share this page": "Κοινοποίηση",
    "Share on Facebook": "Κοινοποίηση στο Facebook",
    "Share on WhatsApp": "Κοινοποίηση στο WhatsApp",
    "Share on X": "Κοινοποίηση στο X",
    "Share by email": "Κοινοποίηση με email",
    "Save &amp; Share": "Αποθήκευση και κοινοποίηση",
    "Breadcrumb": "Διαδρομή",
    "breadcrumb": "διαδρομή",
    "Page navigation": "Σελιδοποίηση",
    "List View": "Λίστα",
    "Map View": "Χάρτης",
    "Map Legend": "Υπόμνημα",
    "Filter by Category": "Φίλτρο κατηγορίας",
    "Filter by Site Type": "Φίλτρο τύπου",
    "All Categories": "Όλες οι κατηγορίες",
    "All categories": "Όλες οι κατηγορίες",
    "All Cities": "Όλες οι πόλεις",
    "All Cuisines": "Όλες οι κουζίνες",
    "All Site Types": "Όλοι οι τύποι",
    "All Types": "Όλοι οι τύποι",
    "Category": "Κατηγορία",
    "Type": "Τύπος",
    "Site Type": "Τύπος χώρου",
    "Location": "Τοποθεσία",
    "Address": "Διεύθυνση",
    "Phone:": "Τηλέφωνο:",
    "Email": "Email",
    "Email:": "Email:",
    "Email Address": "Διεύθυνση email",
    "Website": "Ιστότοπος",
    "Website:": "Ιστότοπος:",
    "Opening Hours": "Ωράριο",
    "Visiting Hours": "Ώρες επίσκεψης",
    "Operating Hours/Season": "Ωράριο / σεζόν",
    "Operating Season": "Περίοδος λειτουργίας",
    "Price": "Τιμή",
    "Price:": "Τιμή:",
    "Price Range": "Εύρος τιμών",
    "Price Range:": "Εύρος τιμών:",
    "Price not available": "Η τιμή δεν είναι διαθέσιμη",
    "Free Access": "Ελεύθερη είσοδος",
    "Rating": "Βαθμολογία",
    "Guest Rating": "Βαθμολογία επισκεπτών",
    "Reviews": "Κριτικές",
    "Difficulty": "Δυσκολία",
    "Difficulty:": "Δυσκολία:",
    "Length": "Μήκος",
    "Length:": "Μήκος:",
    "Duration:": "Διάρκεια:",
    "Elevation Gain:": "Υψομετρική διαφορά:",
    "Est. Time": "Εκτιμώμενος χρόνος",
    "Est. Time:": "Εκτιμώμενος χρόνος:",
    "Best Season:": "Καλύτερη εποχή:",
    "Distance": "Απόσταση",
    "Area": "Περιοχή",
    "Amenities": "Παροχές",
    "Included": "Περιλαμβάνεται",
    "Not Included": "Δεν περιλαμβάνεται",
    "Meeting Point": "Σημείο συνάντησης",
    "Meeting Point Location": "Τοποθεσία συνάντησης",
    "Meetup Location:": "Σημείο συνάντησης:",
    "Trailhead": "Αφετηρία",
    "Trail Map": "Χάρτης μονοπατιού",
    "Trail Quick Info": "Σύντομες πληροφορίες",
    "Tour Information": "Πληροφορίες περιήγησης",
    "Tour Snapshot": "Σύνοψη περιήγησης",
    "Tour Type:": "Τύπος περιήγησης:",
    "Gem Information": "Πληροφορίες",
    "Cafe Information": "Πληροφορίες καφέ",
    "Cafe Type": "Τύπος καφέ",
    "Restaurant Information": "Πληροφορίες εστιατορίου",
    "Cuisine Type": "Είδος κουζίνας",
    "Resort Information": "Πληροφορίες χιονοδρομικού",
    "Ski Resort Type": "Τύπος χιονοδρομικού",
    "Museum Type": "Τύπος μουσείου",
    "Property Type": "Τύπος καταλύματος",
    "Additional Info:": "Επιπλέον πληροφορίες:",
    "Contact Information": "Στοιχεία επικοινωνίας",
    "Contact for Booking": "Επικοινωνία για κράτηση",
    "Reservations & Contact": "Κρατήσεις και επικοινωνία",
    "Near This Site": "Κοντά σε αυτόν τον χώρο",
    "Similar Experiences": "Παρόμοιες εμπειρίες",
    "Loading similar experiences...": "Φόρτωση παρόμοιων εμπειριών...",
    "Details unavailable": "Οι λεπτομέρειες δεν είναι διαθέσιμες",
    "Calculating distance...": "Υπολογισμός απόστασης...",
    "Calculating...": "Υπολογισμός...",
    "Snow Conditions": "Συνθήκες χιονιού",
    "Lift Tickets": "Εισιτήρια αναβατήρων",
    "Traditional Food": "Παραδοσιακό φαγητό",
    "Ancient Sites": "Αρχαίοι χώροι",
    "Trails": "Μονοπάτια",
    "Byzantine": "Βυζαντινό",
    "Any": "Όλα",
    "Other": "Άλλο",
    "From": "Από",
    "Date": "Ημερομηνία",
    "Tips": "Συμβουλές",
    "Show:": "Εμφάνιση:",
    "Ages:": "Ηλικίες:",
    "Availability:": "Διαθεσιμότητα:",
    "Check-in:": "Άφιξη:",
    "Check-out:": "Αναχώρηση:",
    "Departure & Return:": "Αναχώρηση και επιστροφή:",
    "Host Experience:": "Εμπειρία οικοδεσπότη:",
    "Number of travelers": "Αριθμός ατόμων",
    "Accessibility:": "Προσβασιμότητα:",
    "Get in touch": "Επικοινωνήστε μαζί μας",
    "Have questions or suggestions? We'd love to hear from you.": "Έχετε απορίες ή προτάσεις; Θα χαρούμε να τις ακούσουμε.",
    "Send us a message": "Στείλτε μας μήνυμα",
    "Send Message": "Αποστολή",
    "Your Name": "Το όνομά σας",
    "Your Email": "Το email σας",
    "Your Message": "Το μήνυμά σας",
    "Full name": "Ονοματεπώνυμο",
    "Subject": "Θέμα",
    "Please select a topic...": "Επιλέξτε θέμα...",
    "Please specify": "Προσδιορίστε",
    "Tell us how we can help...": "Πείτε μας πώς μπορούμε να βοηθήσουμε...",
    "Brief description of your topic": "Σύντομη περιγραφή",
    "We usually reply within 1–2 business days.": "Απαντάμε συνήθως μέσα σε 1–2 εργάσιμες ημέρες.",
    "Response time": "Χρόνος απάντησης",
    "Monday – Friday, within 48 hours": "Δευτέρα έως Παρασκευή, εντός 48 ωρών",
    "Questions? Email": "Απορίες; Email",
    "Website Feedback": "Σχόλια για τον ιστότοπο",
    "Technical Support": "Τεχνική υποστήριξη",
    "Partnership &amp; Collaboration": "Συνεργασία",
    "Media &amp; Press": "Μέσα και τύπος",
    "General Information about Veria": "Γενικές πληροφορίες για τη Βέροια",
    "Questions about Tourist Attractions": "Ερωτήσεις για αξιοθέατα",
    "Add My Business to VeriaGuide": "Καταχώριση επιχείρησης στο VeriaGuide",
    "I agree to the": "Συμφωνώ με την",
    "Privacy Policy": "Πολιτική απορρήτου",
    "Data Security": "Ασφάλεια δεδομένων",
    "Information": "Πληροφορίες",
    "About": "Σχετικά",
    "Overview": "Επισκόπηση",
    "Service Times": "Ώρες ακολουθιών",
    "Admission Fee": "Εισιτήριο",
    "Special Exhibits": "Ειδικές εκθέσεις",
    "Gallery Information": "Πληροφορίες εκθέσεων",
    "Historical Period": "Ιστορική περίοδος",
    "Why it's a Hidden Gem": "Γιατί είναι κρυμμένος θησαυρός",
    "Best Time to Visit": "Καλύτερη εποχή για επίσκεψη",
    "How to Get There": "Πώς να φτάσετε",
    "Additional Information": "Επιπλέον πληροφορίες",
    "What's Included": "Τι περιλαμβάνεται",
    "Important Information": "Σημαντικές πληροφορίες",
    "Itinerary": "Πρόγραμμα",
    "Trails & Lifts": "Πίστες και αναβατήρες",
    "Signature Dish": "Πιάτο σπεσιαλιτέ",
    "Menu": "Μενού",
    "Menu Highlights": "Προτάσεις μενού",
    "Specialty": "Σπεσιαλιτέ",
    "Coffee Specialties": "Καφέδες",
    "Ambiance": "Ατμόσφαιρα",
    "Food Options": "Φαγητό",
    "Property Highlights": "Χαρακτηριστικά καταλύματος",
    "Most Popular Facilities": "Δημοφιλείς παροχές",
    "Check-in & Check-out": "Άφιξη και αναχώρηση",
    "Attractions": "Αξιοθέατα",
    "Activities": "Δραστηριότητες",
    "Food & Stay": "Φαγητό και διαμονή",
    "Food &amp; Stay": "Φαγητό και διαμονή",
    "Hotels & Accommodations": "Ξενοδοχεία και διαμονή",
    "About Veria": "Σχετικά",
    "Explore by theme": "Εξερευνήστε ανά θέμα",
    "Plan your visit": "Οργανώστε την επίσκεψή σας",
    "Information We Collect": "Πληροφορίες που συλλέγουμε",
    "Religious Affiliation": "Θρησκευτική ένταξη",
    "Visitor Guidelines": "Οδηγίες για επισκέπτες",
    "Last updated:": "Τελευταία ενημέρωση:",
    "Updated": "Ενημερώθηκε",
    "How We Use Your Information": "Πώς χρησιμοποιούμε τις πληροφορίες σας",
    "When you contact us, we collect your name, email, subject, and message.": "Όταν επικοινωνείτε, συλλέγουμε όνομα, email, θέμα και μήνυμα.",
    "We use it to respond to your inquiry and improve our services.": "Τα χρησιμοποιούμε για να απαντήσουμε και να βελτιώσουμε τις υπηρεσίες μας.",
    "We implement appropriate measures to protect your personal information.": "Λαμβάνουμε κατάλληλα μέτρα για την προστασία των προσωπικών σας δεδομένων.",
    "Frequently Asked Questions": "Συχνές ερωτήσεις",
    "What we cover": "Τι καλύπτουμε",
    "Our mission": "Η αποστολή μας",
    "About this guide": "Σχετικά με τον οδηγό",
    "Learn more about VeriaGuide": "Μάθετε περισσότερα για το VeriaGuide",
    "How accurate is the information on VeriaGuide?": "Πόσο ακριβείς είναι οι πληροφορίες στο VeriaGuide;",
    "We verify and update listings regularly. For opening hours and prices, please check official venue websites.": "Ελέγχουμε και ενημερώνουμε τις καταχωρίσεις τακτικά. Για ωράρια και τιμές, δείτε τους επίσημους ιστότοπους.",
    "How can I add my business?": "Πώς καταχωρίζω την επιχείρησή μου;",
    "Select \"Add My Business to VeriaGuide\" in the form and tell us about your venue. We'll follow up with next steps.": "Επιλέξτε «Καταχώριση επιχείρησης στο VeriaGuide» στη φόρμα και περιγράψτε τον χώρο σας. Θα επικοινωνήσουμε για τα επόμενα βήματα.",
    "How do I get around Veria?": "Πώς μετακινούμαι στη Βέροια;",
    "The city centre is walkable. Local buses, taxis, and car hire cover longer distances and the surrounding region.": "Το κέντρο είναι προσβάσιμο με τα πόδια. Λεωφορεία, ταξί και ενοικίαση αυτοκινήτου καλύπτουν μεγαλύτερες αποστάσεις και την ευρύτερη περιοχή.",
    "Is Veria family-friendly?": "Είναι η Βέροια κατάλληλη για οικογένειες;",
    "Yes — many churches, museums, parks, and restaurants welcome families. Look for family-friendly tags in our listings.": "Ναι — πολλοί ναοί, μουσεία, πάρκα και εστιατόρια υποδέχονται οικογένειες. Αναζητήστε τη σχετική σήμανση στις καταχωρίσεις.",
    "When is the best time to visit Veria?": "Πότε είναι η καλύτερη εποχή για τη Βέροια;",
    "Spring and autumn are ideal for sightseeing. Summer suits outdoor activities; winter is great for museums and cozy tavernas.": "Άνοιξη και φθινόπωρο είναι ιδανικά για αξιοθέατα. Το καλοκαίρι ταιριάζει σε υπαίθριες δραστηριότητες, ο χειμώνας σε μουσεία και ταβέρνες.",
    "Transportation &amp; Getting Around": "Μετακινήσεις",
    "Events &amp; Activities": "Εκδηλώσεις και δραστηριότητες",
    "Hotels &amp; Accommodations": "Ξενοδοχεία και διαμονή",
    "Restaurants &amp; Dining": "Εστιατόρια και φαγητό",
    "Your Travel Journey Starts Here": "Το ταξίδι σας ξεκινά εδώ",
    "Sign up and we'll send the best deals to you": "Εγγραφείτε και θα σας στέλνουμε τις καλύτερες προτάσεις",
    "Subscribe": "Εγγραφή",
    "Explore Veria": "Εξερευνήστε τη Βέροια",
    "Explore all locations in Veria": "Όλες οι τοποθεσίες στη Βέροια",
    "Find museums, attractions, restaurants, and more in Veria": "Μουσεία, αξιοθέατα, εστιατόρια και άλλα στη Βέροια",
    "Find the perfect place to stay in Veria and the surrounding area": "Βρείτε πού θα μείνετε στη Βέροια και στα περίχωρα",
    "Discover ancient ruins, temples and historical sites in Veria": "Αρχαία ερείπια, ναοί και ιστορικοί χώροι στη Βέροια",
    "Discover authentic Greek cuisine and dining experiences in Veria": "Αυθεντική ελληνική κουζίνα στη Βέροια",
    "Discover cozy cafes and coffee shops in Veria": "Ζεστά καφέ και καφετέριες στη Βέροια",
    "Discover history, art and culture in Veria's museums": "Ιστορία, τέχνη και πολιτισμός στα μουσεία της Βέροιας",
    "Discover ski resorts and winter sports destinations near Veria": "Χιονοδρομικά και χειμερινός τουρισμός κοντά στη Βέροια",
    "Best Cafes in Veria": "Τα καλύτερα καφέ στη Βέροια",
    "Best Restaurants in Veria": "Τα καλύτερα εστιατόρια στη Βέροια",
    "Byzantine Churches in Veria": "Βυζαντινοί ναοί στη Βέροια",
    "Accommodations in Veria": "Διαμονή στη Βέροια",
    "Archaeological Sites in Veria": "Αρχαιολογικοί χώροι στη Βέροια",
    "Hidden Gems in Veria": "Κρυμμένοι θησαυροί στη Βέροια",
    "Hiking Trails in Veria": "Μονοπάτια στη Βέροια",
    "Museums in Veria": "Μουσεία στη Βέροια",
    "Ski Resorts in Veria": "Χιονοδρομικά κέντρα στη Βέροια",
    "Tours in Veria": "Περιηγήσεις στη Βέροια",
    "Byzantine Churches & Monasteries in Veria, Greece": "Βυζαντινοί ναοί και μοναστήρια στη Βέροια",
    "Byzantine Churches &amp; Monasteries in Veria, Greece": "Βυζαντινοί ναοί και μοναστήρια στη Βέροια",
    "Byzantine Churches &amp; Monasteries Map – Veria, Greece": "Χάρτης βυζαντινών ναών και μοναστηριών – Βέροια",
    "Byzantine churches &amp; monasteries": "Βυζαντινοί ναοί και μοναστήρια",
    "Explore churches and monasteries across Veria (Veroia), Imathia — including sites linked to Apostle Paul.": "Εξερευνήστε ναούς και μοναστήρια στη Βέροια Ημαθίας — και χώρους συνδεδεμένους με τον Απόστολο Παύλο.",
    "Explore sacred sites across Veria (Veroia), Imathia — from centuries-old Byzantine churches to monasteries linked to Apostle Paul's visit.": "Εξερευνήστε ιερούς χώρους στη Βέροια Ημαθίας — από βυζαντινούς ναούς αιώνων έως μοναστήρια συνδεδεμένα με την επίσκεψη του Αποστόλου Παύλου.",
    "Veria is renowned for its extraordinary Byzantine heritage. Find churches near the ancient Vema amphitheatre, check visiting hours and explore every site on the map.": "Η Βέροια φημίζεται για τη βυζαντινή της κληρονομιά. Βρείτε ναούς κοντά στο αρχαίο Βήμα, δείτε ώρες επίσκεψης και εξερευνήστε κάθε χώρο στον χάρτη.",
    "Your trusted guide to Byzantine heritage, museums and archaeological sites in Veria (Veroia), Imathia, Greece.": "Ο οδηγός σας για τη βυζαντινή κληρονομιά, τα μουσεία και τους αρχαιολογικούς χώρους στη Βέροια Ημαθίας.",
    "VeriaGuide helps visitors discover the cultural heart of Macedonia — from Byzantine churches and monasteries to museums and archaeological landmarks linked to the legacy of Apostle Paul and the ancient kingdom of Macedon.": "Το VeriaGuide βοηθά τους επισκέπτες να γνωρίσουν την πολιτιστική καρδιά της Μακεδονίας — από βυζαντινούς ναούς και μοναστήρια έως μουσεία και αρχαιολογικά μνημεία του Αποστόλου Παύλου και του αρχαίου βασιλείου των Μακεδόνων.",
    "We publish practical, accurate travel information for heritage-focused visitors: opening hours, maps, directions and historical context — so you can plan meaningful visits across Veria and Imathia.": "Δημοσιεύουμε πρακτικές και ακριβείς ταξιδιωτικές πληροφορίες: ωράρια, χάρτες, οδηγίες και ιστορικό πλαίσιο, για να οργανώσετε ουσιαστικές επισκέψεις στη Βέροια και την Ημαθία.",
    "Researched and written by the": "Έρευνα και κείμενο από τη",
    "editorial team, with a focus on Byzantine heritage, local history and practical visitor information for Veria (Veroia), Imathia.": "συντακτική ομάδα, με έμφαση στη βυζαντινή κληρονομιά, την τοπική ιστορία και πρακτικές πληροφορίες για τη Βέροια Ημαθίας.",
    "No accommodations found. Please check back later.": "Δεν βρέθηκαν καταλύματα. Δοκιμάστε ξανά αργότερα.",
    "No archaeological sites found matching your criteria.": "Δεν βρέθηκαν αρχαιολογικοί χώροι με αυτά τα κριτήρια.",
    "No cafes found matching your criteria.": "Δεν βρέθηκαν καφέ με αυτά τα κριτήρια.",
    "No hidden gems found. Please check back later.": "Δεν βρέθηκαν κρυμμένοι θησαυροί. Δοκιμάστε ξανά αργότερα.",
    "No hiking trails found. Please check back later.": "Δεν βρέθηκαν μονοπάτια. Δοκιμάστε ξανά αργότερα.",
    "No museums found matching your criteria.": "Δεν βρέθηκαν μουσεία με αυτά τα κριτήρια.",
    "No religious sites found matching your criteria.": "Δεν βρέθηκαν θρησκευτικοί χώροι με αυτά τα κριτήρια.",
    "No religious sites found. Please check back later.": "Δεν βρέθηκαν θρησκευτικοί χώροι. Δοκιμάστε ξανά αργότερα.",
    "No restaurants found matching your criteria.": "Δεν βρέθηκαν εστιατόρια με αυτά τα κριτήρια.",
    "No ski_resorts found matching your criteria.": "Δεν βρέθηκαν χιονοδρομικά κέντρα με αυτά τα κριτήρια.",
    "No tours found. Please check back later.": "Δεν βρέθηκαν περιηγήσεις. Δοκιμάστε ξανά αργότερα.",
    "Search archaeological sites...": "Αναζήτηση αρχαιολογικών χώρων...",
    "Search attractions, restaurants, activities...": "Αξιοθέατα, εστιατόρια, δραστηριότητες...",
    "Search by name or category": "Αναζήτηση με όνομα ή κατηγορία",
    "Search by name": "Αναζήτηση με όνομα",
    "Search by tour name": "Αναζήτηση περιήγησης",
    "Search by trail name": "Αναζήτηση μονοπατιού",
    "Search cafes...": "Αναζήτηση καφέ...",
    "Search churches, museums, Vergina…": "Ναοί, μουσεία, Βεργίνα…",
    "Search for anything...": "Αναζήτηση...",
    "Search museums...": "Αναζήτηση μουσείων...",
    "Search religious sites...": "Αναζήτηση θρησκευτικών χώρων...",
    "Search restaurants...": "Αναζήτηση εστιατορίων...",
    "Search ski_resorts...": "Αναζήτηση χιονοδρομικών...",
    "Search in all categories": "Αναζήτηση σε όλες τις κατηγορίες",
    "e.g. Aliakmonas": "π.χ. Αλιάκμονας",
    "e.g. City Walking Tour": "π.χ. Περίπατος στην πόλη",
    "e.g. Kato Vermio": "π.χ. Κάτω Βέρμιο",
    "Hand-picked highlights from Veria": "Επιλεγμένα σημεία από τη Βέροια",
    "Cultural treasures and local history": "Πολιτιστικοί θησαυροί και τοπική ιστορία",
    "Ancient ruins and archaeological wonders": "Αρχαία ερείπια και αρχαιολογικοί χώροι",
    "Byzantine churches and monasteries — Apostle Paul's legacy in Veria": "Βυζαντινοί ναοί και μοναστήρια — η κληρονομιά του Αποστόλου Παύλου στη Βέροια",
    "Byzantine church in Veria, Greece": "βυζαντινός ναός στη Βέροια",
    "museum in Veria, Imathia, Greece": "μουσείο στη Βέροια Ημαθίας",
    "archaeological site near Veria, Greece": "αρχαιολογικός χώρος κοντά στη Βέροια",
    "Veria Guide listing": "καταχώριση Veria Guide",
    "Get in touch with the VeriaGuide team": "Επικοινωνήστε με την ομάδα του VeriaGuide",
    "Interactive Map of Veria": "Διαδραστικός χάρτης της Βέροιας",
    "Explore Veria's attractions, restaurants, and more on our interactive map": "Αξιοθέατα, εστιατόρια και άλλα στον διαδραστικό χάρτη",
    "Byzantine Churches Map – Veria, Greece": "Χάρτης βυζαντινών ναών – Βέροια",
    "Map of Byzantine churches and monasteries in Veria (Veroia), Imathia, Greece. Find sacred sites, plan visits and explore Apostle Paul's legacy.": "Χάρτης βυζαντινών ναών και μοναστηριών στη Βέροια Ημαθίας. Βρείτε ιερούς χώρους και οργανώστε την επίσκεψή σας.",
    "Learn about VeriaGuide — your local travel guide to Veria (Veroia), Imathia, Greece. Byzantine churches, museums, archaeological sites and Macedonian heritage.": "Μάθετε για το VeriaGuide, τον τοπικό οδηγό για τη Βέροια Ημαθίας: βυζαντινοί ναοί, μουσεία, αρχαιολογικοί χώροι και μακεδονική κληρονομιά.",
    "Veria Greece Travel Guide – Churches, Museums & Vergina": "Ταξιδιωτικός οδηγός Βέροιας – ναοί, μουσεία και Βεργίνα",
    "Plan your trip to Veria (Veroia), Imathia, Greece: Byzantine churches, museums, Royal Tombs of Vergina, archaeological sites and Apostle Paul's legacy in Macedonia.": "Οργανώστε το ταξίδι σας στη Βέροια Ημαθίας: βυζαντινοί ναοί, μουσεία, οι βασιλικοί τάφοι της Βεργίνας, αρχαιολογικοί χώροι και η κληρονομιά του Αποστόλου Παύλου στη Μακεδονία.",
    "Veria, Greece: Byzantine Churches & Macedonian Heritage": "Βέροια: βυζαντινοί ναοί και μακεδονική κληρονομιά",
    "Explore Veria (Veroia) in Imathia — 60+ Byzantine churches, museums, Royal Tombs of Vergina and the Vema where Apostle Paul preached.": "Εξερευνήστε τη Βέροια στην Ημαθία — πάνω από 60 βυζαντινούς ναούς, μουσεία, τους βασιλικούς τάφους της Βεργίνας και το Βήμα όπου κήρυξε ο Απόστολος Παύλος.",
    "<p>Discover Veria (Veroia), a historic city in Imathia, northern Greece, where Byzantine churches, museums and archaeological treasures meet Macedonian heritage. Use Veria Guide to explore churches linked to Apostle Paul, the Royal Tombs of Vergina and hidden gems across the region.</p>": "<p>Ανακαλύψτε τη Βέροια, μια ιστορική πόλη στην Ημαθία, στη βόρεια Ελλάδα, όπου βυζαντινοί ναοί, μουσεία και αρχαιολογικοί θησαυροί συναντούν τη μακεδονική κληρονομιά. Με τον Veria Guide εξερευνάτε ναούς συνδεδεμένους με τον Απόστολο Παύλο, τους βασιλικούς τάφους της Βεργίνας και κρυμμένους θησαυρούς της περιοχής.</p>",
    "Explore Byzantine churches and monasteries in Veria (Veroia), Imathia — including sites linked to Apostle Paul. Visiting hours, maps and travel guide.": "Βυζαντινοί ναοί και μοναστήρια στη Βέροια Ημαθίας — και χώροι συνδεδεμένοι με τον Απόστολο Παύλο. Ώρες επίσκεψης, χάρτες και οδηγός.",
    "Museums in Veria, Greece": "Μουσεία στη Βέροια",
    "Discover the history of Veria: from Byzantine treasures to the Archaeological Museum. Opening hours, admission and insider tips for your visit in Imathia, Macedonia.": "Η ιστορία της Βέροιας: από βυζαντινούς θησαυρούς έως το Αρχαιολογικό Μουσείο. Ωράριο, εισιτήρια και συμβουλές για την επίσκεψη στην Ημαθία.",
    "Archaeological Sites in Veria, Greece": "Αρχαιολογικοί χώροι στη Βέροια",
    "Explore ancient Veria and Vergina: archaeological sites, ruins and heritage landmarks in Imathia. Maps, visiting tips and travel guide for history lovers.": "Η αρχαία Βέροια και η Βεργίνα: αρχαιολογικοί χώροι, ερείπια και μνημεία στην Ημαθία. Χάρτες και συμβουλές επίσκεψης.",
    "Tours in Veria, Greece": "Περιηγήσεις στη Βέροια",
    "Hiking Trails in Veria, Greece": "Μονοπάτια στη Βέροια",
    "Hidden Gems in Veria, Greece": "Κρυμμένοι θησαυροί στη Βέροια",
    "Ski Resorts in Veria, Greece": "Χιονοδρομικά κέντρα στη Βέροια",
    "Accommodations in Veria, Greece": "Διαμονή στη Βέροια",
    "Restaurants in Veria, Greece": "Εστιατόρια στη Βέροια",
    "Cafes in Veria, Greece": "Καφέ στη Βέροια",
    "Discover the best tours in Veria (Veroia), Imathia, Greece.": "Περιηγήσεις στη Βέροια Ημαθίας.",
    "Discover the best hiking trails in Veria (Veroia), Imathia, Greece.": "Μονοπάτια πεζοπορίας στη Βέροια Ημαθίας.",
    "Discover the best hidden gems in Veria (Veroia), Imathia, Greece.": "Κρυμμένοι θησαυροί στη Βέροια Ημαθίας.",
    "Discover the best ski resorts in Veria (Veroia), Imathia, Greece.": "Χιονοδρομικά κέντρα κοντά στη Βέροια Ημαθίας.",
    "Discover the best accommodations in Veria (Veroia), Imathia, Greece.": "Καταλύματα στη Βέροια Ημαθίας.",
    "Discover the best restaurants in Veria (Veroia), Imathia, Greece.": "Εστιατόρια στη Βέροια Ημαθίας.",
    "Discover the best cafes in Veria (Veroia), Imathia, Greece.": "Καφέ στη Βέροια Ημαθίας.",
    "Thank you for your message! We'll get back to you within 24 hours.": "Ευχαριστούμε για το μήνυμά σας. Θα απαντήσουμε μέσα σε 24 ώρες.",
    "All fields are required. Please fill out the complete form.": "Όλα τα πεδία είναι υποχρεωτικά.",
    "The contact form is temporarily unavailable. Please email us directly.": "Η φόρμα είναι προσωρινά μη διαθέσιμη. Στείλτε μας απευθείας email.",
    "Sorry, there was a temporary issue sending your message. Please try again.": "Παρουσιάστηκε προσωρινό πρόβλημα στην αποστολή. Δοκιμάστε ξανά.",
    "Religious Site": "Θρησκευτικός χώρος",
    "Museum": "Μουσείο",
    "Archaeological Site": "Αρχαιολογικός χώρος",
    "Hiking Trail": "Μονοπάτι",
    "Restaurant": "Εστιατόριο",
    "Cafe": "Καφέ",
    "Accommodation": "Κατάλυμα",
    "Ski Resort": "Χιονοδρομικό κέντρο",
    "Tour": "Περιήγηση",
    "Hidden Gem": "Κρυμμένος θησαυρός",
}
