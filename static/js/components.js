/* ═══════════════════════════════════════════
   COMPONENTS — Reusable rendering functions
   ═══════════════════════════════════════════ */

// ── Narxni formatlash ──
function formatPrice(price) {
    const num = parseFloat(price);
    if (isNaN(num)) return "0";
    return num.toLocaleString("uz-UZ", { maximumFractionDigits: 0 });
}

// ── Status badge ──
function statusBadge(st) {
    const map = {
        pending: "Kutilyapti",
        agreed: "Kelishilgan",
        completed: "Sotib olingan",
        canceled: "Bekor qilingan",
        active: "Aktiv",
        moderation: "Moderatsiyada",
        rejected: "Rad etilgan",
        sold: "Sotilgan",
        archived: "Arxivlangan",
    };
    return '<span class="status-badge status-' + st + '">' + (map[st] || st) + '</span>';
}

// ── Kategoriya iconlari ──
function categoryIcon(type) {
    const map = {
        phone: "fa-mobile-alt",
        tv: "fa-tv",
        laptop: "fa-laptop",
        clothing: "fa-tshirt",
        shoes: "fa-shoe-prints",
        appliance: "fa-blender",
        auto: "fa-car",
        food: "fa-apple-alt",
        furniture: "fa-couch",
        book: "fa-book",
        hobby: "fa-gamepad",
        other: "fa-box-open",
    };
    return map[type] || "fa-box-open";
}

// ── Yulduzlar ──
function starsHtml(rating) {
    var html = "";
    for (var i = 1; i <= 5; i++) {
        if (i <= Math.round(rating)) {
            html += '<i class="fas fa-star"></i>';
        } else {
            html += '<i class="far fa-star"></i>';
        }
    }
    return html;
}

// ── Rasm URL ──
function imageUrl(path) {
    if (!path) return null;
    if (path.startsWith("http")) return path;
    const backendUrl = (window.APP_CONFIG && window.APP_CONFIG.BACKEND_URL) 
        ? window.APP_CONFIG.BACKEND_URL 
        : "http://127.0.0.1:8000";
    return backendUrl + path;
}

// ── HTML escape ──
function escHtml(str) {
    if (!str) return "";
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

// ── Mahsulot kartochkasi ──
function renderProductCard(product) {
    var mainImg = null;
    if (product.images && product.images.length) {
        mainImg = product.images.find(function(i) { return i.is_main; }) || product.images[0];
    }

    var imgHtml = mainImg
        ? '<img class="product-card__img" src="' + imageUrl(mainImg.image) + '" alt="' + escHtml(product.title) + '" loading="lazy">'
        : '<div class="product-card__img-placeholder"><i class="fas fa-image"></i></div>';

    var displayPrice = product.price_with_tax || product.price;
    var hasTax = product.tax_percent && parseFloat(product.tax_percent) > 0;

    var taxInfo = "";
    if (hasTax) {
        taxInfo = '<span class="product-card__price-original">(' + formatPrice(product.price) + ' + soliq)</span>';
    }

    return '<div class="product-card" onclick="showProductDetail(' + product.id + ')">' +
        imgHtml +
        '<div class="product-card__body">' +
            '<div class="product-card__title">' + escHtml(product.title) + '</div>' +
            '<div class="product-card__price">' + formatPrice(displayPrice) + " so'm " + taxInfo + '</div>' +
            '<div class="product-card__meta">' +
                '<span><i class="fas fa-eye"></i> ' + product.view_count + '</span>' +
                '<span><i class="fas fa-heart"></i> ' + product.favorite_count + '</span>' +
            '</div>' +
        '</div>' +
    '</div>';
}

// ── Products grid ──
function renderProductsGrid(products) {
    if (!products || !products.length) {
        return '<div class="empty-state">' +
            '<i class="fas fa-search"></i>' +
            '<p>Mahsulotlar topilmadi</p>' +
            '<span style="color:var(--text-secondary);font-size:.85rem;">Boshqa filtrlarni sinab ko\'ring</span>' +
        '</div>';
    }
    return '<div class="products-grid">' + products.map(renderProductCard).join("") + '</div>';
}

// ── Pagination ──
function renderPagination(data) {
    if (!data.next && !data.previous) return "";
    var html = '<div class="pagination">';
    if (data.previous) {
        html += '<button onclick="loadPage(\'' + data.previous + '\')"><i class="fas fa-chevron-left"></i> Oldingi</button>';
    }
    if (data.next) {
        html += '<button onclick="loadPage(\'' + data.next + '\')">Keyingi <i class="fas fa-chevron-right"></i></button>';
    }
    html += "</div>";
    return html;
}

// ── Toast xabarnoma ──
function toast(message, type) {
    type = type || "info";
    var el = document.getElementById("toast");
    el.textContent = message;
    el.className = "toast " + type + " show";
    setTimeout(function() { el.className = "toast"; }, 3500);
}

// ── Modal ──
function openModal(id) {
    var modal = document.getElementById(id);
    if (modal) {
        modal.classList.add("show");
        modal.style.display = "flex";
        document.body.style.overflow = "hidden";
    }
}

function closeModal(id) {
    console.log("closeModal chaqirildi, id:", id);
    var modal = document.getElementById(id);
    console.log("Modal topildi:", modal);
    if (modal) {
        modal.classList.remove("show");
        modal.style.display = "none";
        document.body.style.overflow = "";
        
        // Dinamik yaratilgan modallarni DOM dan o'chirish
        if (id === 'orderModal') {
            modal.remove();
            console.log("orderModal DOM dan o'chirildi");
            // Global o'zgaruvchilarni tozalash
            if (typeof orderProductId !== 'undefined') orderProductId = null;
            if (typeof isOrderSubmitting !== 'undefined') isOrderSubmitting = false;
        }
    } else {
        console.log("Modal topilmadi:", id);
    }
}

// ── Attribute specs renderer ──
function renderAttributeSpecs(product) {
    var html = "";

    // 📱 Telefon
    if (product.phone_attr) {
        var a = product.phone_attr;
        if (a.model_name) html += "<dt>Model</dt><dd>" + escHtml(a.model_name) + "</dd>";
        if (a.color) html += "<dt>Rang</dt><dd>" + a.color.name + "</dd>";
        if (a.storage_gb) html += "<dt>Xotira</dt><dd>" + a.storage_gb + " GB</dd>";
        if (a.ram_gb) html += "<dt>RAM</dt><dd>" + a.ram_gb + " GB</dd>";
        if (a.battery_mah) html += "<dt>Batareya</dt><dd>" + a.battery_mah + " mAh</dd>";
        if (a.screen_size) html += '<dt>Ekran</dt><dd>' + a.screen_size + '"</dd>';
        if (a.os) html += "<dt>OS</dt><dd>" + a.os + "</dd>";
        if (a.sim_count) html += "<dt>SIM</dt><dd>" + a.sim_count + " ta</dd>";
        if (a.camera_mp) html += "<dt>Kamera</dt><dd>" + a.camera_mp + " MP</dd>";
    }

    // 📺 Televizor
    if (product.tv_attr) {
        var b = product.tv_attr;
        if (b.model_name) html += "<dt>Model</dt><dd>" + escHtml(b.model_name) + "</dd>";
        if (b.color) html += "<dt>Rang</dt><dd>" + b.color.name + "</dd>";
        if (b.screen_size) html += '<dt>Ekran</dt><dd>' + b.screen_size + '"</dd>';
        if (b.resolution) html += "<dt>Ruxsat</dt><dd>" + b.resolution + "</dd>";
        if (b.is_smart) html += "<dt>Smart TV</dt><dd>Ha ✅</dd>";
        if (b.refresh_rate) html += "<dt>Hz</dt><dd>" + b.refresh_rate + " Hz</dd>";
        if (b.warranty_months) html += "<dt>Kafolat</dt><dd>" + b.warranty_months + " oy</dd>";
    }

    // 💻 Noutbuk
    if (product.laptop_attr) {
        var c = product.laptop_attr;
        if (c.model_name) html += "<dt>Model</dt><dd>" + escHtml(c.model_name) + "</dd>";
        if (c.color) html += "<dt>Rang</dt><dd>" + c.color.name + "</dd>";
        if (c.processor) html += "<dt>Protsessor</dt><dd>" + escHtml(c.processor) + "</dd>";
        if (c.ram_gb) html += "<dt>RAM</dt><dd>" + c.ram_gb + " GB</dd>";
        if (c.storage_gb) html += "<dt>Xotira</dt><dd>" + c.storage_gb + " GB" + (c.storage_type ? " (" + c.storage_type + ")" : "") + "</dd>";
        if (c.screen_size) html += '<dt>Ekran</dt><dd>' + c.screen_size + '"</dd>';
        if (c.battery_hours) html += "<dt>Batareya</dt><dd>~" + c.battery_hours + " soat</dd>";
        if (c.os) html += "<dt>OS</dt><dd>" + c.os + "</dd>";
        if (c.warranty_months) html += "<dt>Kafolat</dt><dd>" + c.warranty_months + " oy</dd>";
    }

    // 👕 Kiyim
    if (product.clothing_attr) {
        var d = product.clothing_attr;
        if (d.available_sizes && d.available_sizes.length) {
            html += "<dt>Razmerlar</dt><dd>" + d.available_sizes.map(function(s) {
                return '<span class="size-badge">' + escHtml(s) + '</span>';
            }).join(" ") + "</dd>";
        }
        if (d.gender) html += "<dt>Jins</dt><dd>" + d.gender + "</dd>";
        if (d.color) html += "<dt>Rang</dt><dd>" + d.color.name + "</dd>";
        if (d.material) html += "<dt>Material</dt><dd>" + escHtml(d.material) + "</dd>";
        if (d.season) html += "<dt>Mavsim</dt><dd>" + d.season + "</dd>";
    }

    // 👟 Oyoq kiyim
    if (product.shoes_attr) {
        var e = product.shoes_attr;
        if (e.available_sizes && e.available_sizes.length) {
            html += "<dt>Razmerlar</dt><dd>" + e.available_sizes.map(function(s) {
                return '<span class="size-badge">' + s + '</span>';
            }).join(" ") + "</dd>";
        }
        if (e.gender) html += "<dt>Jins</dt><dd>" + e.gender + "</dd>";
        if (e.color) html += "<dt>Rang</dt><dd>" + e.color.name + "</dd>";
        if (e.material) html += "<dt>Material</dt><dd>" + escHtml(e.material) + "</dd>";
        if (e.season) html += "<dt>Mavsim</dt><dd>" + e.season + "</dd>";
    }

    // 🏠 Maishiy texnika
    if (product.appliance_attr) {
        var f = product.appliance_attr;
        if (f.model_name) html += "<dt>Model</dt><dd>" + escHtml(f.model_name) + "</dd>";
        if (f.color) html += "<dt>Rang</dt><dd>" + f.color.name + "</dd>";
        if (f.power_watt) html += "<dt>Quvvat</dt><dd>" + f.power_watt + " Vt</dd>";
        if (f.energy_class) html += "<dt>Energiya sinfi</dt><dd>" + f.energy_class + "</dd>";
        if (f.weight_kg) html += "<dt>Og'irligi</dt><dd>" + f.weight_kg + " kg</dd>";
        if (f.dimensions) html += "<dt>O'lcham</dt><dd>" + f.dimensions + "</dd>";
        if (f.warranty_months) html += "<dt>Kafolat</dt><dd>" + f.warranty_months + " oy</dd>";
    }

    // 🚗 Avtomobil
    if (product.auto_attr) {
        var g = product.auto_attr;
        if (g.make) html += "<dt>Marka</dt><dd>" + escHtml(g.make) + "</dd>";
        if (g.model_name) html += "<dt>Model</dt><dd>" + escHtml(g.model_name) + "</dd>";
        if (g.year) html += "<dt>Yil</dt><dd>" + g.year + "</dd>";
        if (g.color) html += "<dt>Rang</dt><dd>" + g.color.name + "</dd>";
        if (g.fuel_type) html += "<dt>Yoqilg'i</dt><dd>" + g.fuel_type + "</dd>";
        if (g.transmission) html += "<dt>Uzatma</dt><dd>" + g.transmission + "</dd>";
        if (g.drive_type) html += "<dt>Yurish</dt><dd>" + g.drive_type + "</dd>";
        if (g.mileage_km) html += "<dt>Probeg</dt><dd>" + g.mileage_km.toLocaleString() + " km</dd>";
        if (g.engine_cc) html += "<dt>Motor</dt><dd>" + g.engine_cc + " cc</dd>";
    }

    // 🍎 Oziq-ovqat
    if (product.food_attr) {
        var h = product.food_attr;
        if (h.expiry_date) html += "<dt>Yaroqlilik</dt><dd>" + h.expiry_date + "</dd>";
        if (h.weight) html += "<dt>Og'irligi</dt><dd>" + h.weight + " " + h.weight_unit + "</dd>";
        if (h.is_organic) html += "<dt>Organik</dt><dd>Ha ✅</dd>";
        if (h.ingredients) html += "<dt>Tarkibi</dt><dd>" + escHtml(h.ingredients) + "</dd>";
        if (h.storage_info) html += "<dt>Saqlash</dt><dd>" + escHtml(h.storage_info) + "</dd>";
    }

    // 🪑 Mebel
    if (product.furniture_attr) {
        var i = product.furniture_attr;
        if (i.material) html += "<dt>Material</dt><dd>" + escHtml(i.material) + "</dd>";
        if (i.color) html += "<dt>Rang</dt><dd>" + i.color.name + "</dd>";
        if (i.dimensions) html += "<dt>O'lcham</dt><dd>" + i.dimensions + "</dd>";
        if (i.weight_kg) html += "<dt>Og'irligi</dt><dd>" + i.weight_kg + " kg</dd>";
        if (i.warranty_months) html += "<dt>Kafolat</dt><dd>" + i.warranty_months + " oy</dd>";
    }

    // 📚 Kitob
    if (product.book_attr) {
        var j = product.book_attr;
        if (j.author) html += "<dt>Muallif</dt><dd>" + escHtml(j.author) + "</dd>";
        if (j.publisher) html += "<dt>Nashriyot</dt><dd>" + escHtml(j.publisher) + "</dd>";
        if (j.language) html += "<dt>Til</dt><dd>" + escHtml(j.language) + "</dd>";
        if (j.pages) html += "<dt>Sahifalar</dt><dd>" + j.pages + "</dd>";
        if (j.isbn) html += "<dt>ISBN</dt><dd>" + j.isbn + "</dd>";
        if (j.genre) html += "<dt>Janr</dt><dd>" + escHtml(j.genre) + "</dd>";
    }

    // 🎮 Hobbi
    if (product.hobby_attr) {
        var k = product.hobby_attr;
        if (k.hobby_type) html += "<dt>Turi</dt><dd>" + escHtml(k.hobby_type) + "</dd>";
        if (k.age_min || k.age_max) html += "<dt>Yosh</dt><dd>" + (k.age_min || "?") + " — " + (k.age_max || "?") + " yosh</dd>";
        if (k.material) html += "<dt>Material</dt><dd>" + escHtml(k.material) + "</dd>";
    }

    // 🔧 Boshqa
    if (product.other_attr) {
        var l = product.other_attr;
        if (l.material) html += "<dt>Material</dt><dd>" + escHtml(l.material) + "</dd>";
        if (l.color) html += "<dt>Rang</dt><dd>" + l.color.name + "</dd>";
        if (l.weight_kg) html += "<dt>Og'irligi</dt><dd>" + l.weight_kg + " kg</dd>";
        if (l.warranty_months) html += "<dt>Kafolat</dt><dd>" + l.warranty_months + " oy</dd>";
    }

    return html;
}
