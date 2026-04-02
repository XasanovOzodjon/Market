/* ═══════════════════════════════════════════
   SELLER.JS — Seller Panel Logic
   ═══════════════════════════════════════════ */

var sellerActivePage = "dashboard";

// ═══════════════ INIT ═══════════════
document.addEventListener("DOMContentLoaded", function () {
    // Seller panel — o'z init
    initSellerPanel();
});

async function initSellerPanel() {
    // Auth tekshirish
    if (!isLoggedIn()) {
        showAuthModal();
        return;
    }

    if (!currentUser) {
        await fetchCurrentUser();
    }

    // Faqat sotuvchilar
    if (!currentUser || currentUser.role !== "seller") {
        document.getElementById("sellerContent").innerHTML =
            '<div class="empty-state" style="margin-top:60px">' +
                '<i class="fas fa-store-slash" style="font-size:3rem;color:var(--danger)"></i>' +
                '<h3 style="margin-top:16px">Ruxsat yo\'q</h3>' +
                '<p style="color:var(--text-secondary)">Bu sahifa faqat sotuvchilar uchun.</p>' +
                '<a href="/" class="btn btn-primary" style="margin-top:16px"><i class="fas fa-home"></i> Bosh sahifaga</a>' +
            '</div>';
        return;
    }

    // Topbar — user info
    document.getElementById("sellerUsername").textContent = currentUser.username || "";
    document.getElementById("sellerAvatar").textContent =
        currentUser.username ? currentUser.username[0].toUpperCase() : "S";

    // Kategoriyalar keshini yuklash
    if (!categoriesCache || categoriesCache.length === 0) {
        try {
            categoriesCache = await api.get("/categories/");
        } catch (e) {
            console.error("Kategoriyalar yuklanmadi:", e);
        }
    }

    // Price preview setup
    setupPricePreview();

    // Dashboard ko'rsatish
    sellerGoHome();
}

// ═══════════════ NAV STATE ═══════════════
function setSellerNav(page) {
    sellerActivePage = page;
    var links = document.querySelectorAll("#sellerNav a");
    links.forEach(function (a) {
        if (a.getAttribute("data-page") === page) {
            a.classList.add("active");
        } else {
            a.classList.remove("active");
        }
    });

    // Close mobile sidebar on nav
    var sidebar = document.getElementById("sellerSidebar");
    if (sidebar.classList.contains("open")) {
        sidebar.classList.remove("open");
    }
}

function setSellerTopbar(title, subtitle) {
    document.getElementById("sellerPageTitle").textContent = title;
    document.getElementById("sellerPageSubtitle").textContent = subtitle || "";
}

function toggleSellerSidebar() {
    document.getElementById("sellerSidebar").classList.toggle("open");
}

// ═══════════════ DASHBOARD ═══════════════
async function sellerGoHome() {
    setSellerNav("dashboard");
    setSellerTopbar("Dashboard", "Statistika va umumiy ma'lumotlar");

    var content = document.getElementById("sellerContent");
    content.innerHTML = '<div class="loader"><div class="spinner"></div></div>';

    try {
        // Fetch seller data + products + orders in parallel
        var sellerRes = await api.get("/sellers/" + currentUser.id + "/");
        var seller = sellerRes.seller;

        var prodsRes = await api.get("/sellers/" + currentUser.id + "/products/");
        var products = prodsRes.products || prodsRes;

        var orders = [];
        try {
            orders = await api.get("/orders/");
        } catch (e) { /* no orders */ }

        // Stats
        var totalProducts = products ? products.length : 0;
        var activeProducts = products ? products.filter(function (p) { return p.status === "active"; }).length : 0;
        var moderationProducts = products ? products.filter(function (p) { return p.status === "moderation"; }).length : 0;

        var sellerOrders = orders ? orders.filter(function (o) {
            return o.seller === currentUser.id;
        }) : [];
        var pendingOrders = sellerOrders.filter(function (o) { return o.status === "pending"; }).length;
        var completedOrders = sellerOrders.filter(function (o) { return o.status === "completed"; }).length;

        var html =
            '<div class="stats-grid">' +
                '<div class="stat-card">' +
                    '<div class="stat-card__icon purple"><i class="fas fa-box-open"></i></div>' +
                    '<div class="stat-card__info"><h3>' + totalProducts + '</h3><p>Jami mahsulotlar</p></div>' +
                '</div>' +
                '<div class="stat-card">' +
                    '<div class="stat-card__icon green"><i class="fas fa-check-circle"></i></div>' +
                    '<div class="stat-card__info"><h3>' + activeProducts + '</h3><p>Aktiv e\'lonlar</p></div>' +
                '</div>' +
                '<div class="stat-card">' +
                    '<div class="stat-card__icon orange"><i class="fas fa-clock"></i></div>' +
                    '<div class="stat-card__info"><h3>' + pendingOrders + '</h3><p>Kutilayotgan buyurtmalar</p></div>' +
                '</div>' +
                '<div class="stat-card">' +
                    '<div class="stat-card__icon blue"><i class="fas fa-shopping-cart"></i></div>' +
                    '<div class="stat-card__info"><h3>' + completedOrders + '</h3><p>Yakunlangan sotuvlar</p></div>' +
                '</div>' +
            '</div>';

        // Moderation alert
        if (moderationProducts > 0) {
            html += '<div class="panel-card" style="margin-bottom:20px;border-left:4px solid #f97316">' +
                '<div class="panel-card__body" style="display:flex;align-items:center;gap:12px">' +
                    '<i class="fas fa-exclamation-circle" style="font-size:1.5rem;color:#f97316"></i>' +
                    '<div>' +
                        '<strong>' + moderationProducts + ' ta mahsulot moderatsiyada</strong>' +
                        '<p style="margin:2px 0 0;font-size:.85rem;color:var(--text-secondary)">Admin tekshiruvidan o\'tishi kutilmoqda</p>' +
                    '</div>' +
                '</div>' +
            '</div>';
        }

        // Seller info card
        html += '<div class="panel-card" style="margin-bottom:20px">' +
            '<div class="panel-card__header"><h2><i class="fas fa-store"></i> Do\'kon ma\'lumotlari</h2></div>' +
            '<div class="panel-card__body">' +
                '<dl class="detail-specs">' +
                    '<dt>Do\'kon nomi</dt><dd>' + escHtml(seller.shop_name || "—") + '</dd>' +
                    '<dt>Reyting</dt><dd>' + starsHtml(seller.rating || 0) + ' (' + (seller.rating || 0).toFixed(1) + ')</dd>' +
                    '<dt>Jami sotilgan</dt><dd>' + (seller.total_sales || 0) + ' ta</dd>' +
                    (seller.region ? '<dt>Viloyat</dt><dd>' + escHtml(seller.region) + '</dd>' : '') +
                    (seller.district ? '<dt>Tuman</dt><dd>' + escHtml(seller.district) + '</dd>' : '') +
                '</dl>' +
            '</div>' +
        '</div>';

        // Recent products
        if (products && products.length > 0) {
            html += '<div class="panel-card">' +
                '<div class="panel-card__header">' +
                    '<h2><i class="fas fa-clock"></i> So\'nggi e\'lonlar</h2>' +
                    '<button class="btn btn-outline btn-sm" onclick="sellerShowProducts()">Barchasini ko\'rish</button>' +
                '</div>' +
                '<div class="panel-card__body">';

            var recentProds = products.slice(0, 5);
            html += '<div class="orders-list">';
            recentProds.forEach(function (p) {
                var img = (p.images && p.images.length) ? p.images[0] : null;
                var imgTag = img
                    ? '<img class="order-card__img" src="' + imageUrl(img.image) + '">'
                    : '<div class="order-card__img" style="display:flex;align-items:center;justify-content:center;background:var(--bg)"><i class="fas fa-image"></i></div>';

                html += '<div class="order-card">' +
                    imgTag +
                    '<div class="order-card__info">' +
                        '<div class="order-card__title">' + escHtml(p.title) + '</div>' +
                        '<div class="order-card__meta">' +
                            statusBadge(p.status) + ' · ' +
                            formatPrice(p.price_with_tax || p.price) + " so'm · " +
                            new Date(p.created_at).toLocaleDateString("uz-UZ") +
                        '</div>' +
                    '</div>' +
                '</div>';
            });
            html += '</div></div></div>';
        }

        content.innerHTML = html;

    } catch (e) {
        console.error("Dashboard yuklanmadi:", e);
        content.innerHTML =
            '<div class="empty-state">' +
                '<i class="fas fa-exclamation-triangle"></i>' +
                '<p>Dashboard yuklanmadi</p>' +
                '<p style="color:var(--text-secondary);font-size:.85rem">Avval sotuvchi profilini yarating yoki admin bilan bog\'laning.</p>' +
            '</div>';
    }
}

// ═══════════════ MY PRODUCTS ═══════════════
async function sellerShowProducts() {
    setSellerNav("products");
    setSellerTopbar("Mahsulotlarim", "Barcha e'lonlaringiz ro'yxati");

    var content = document.getElementById("sellerContent");
    content.innerHTML = '<div class="loader"><div class="spinner"></div></div>';

    try {
        var data = await api.get("/sellers/" + currentUser.id + "/products/");
        var products = data.products || data;

        var html = '<div class="panel-card">' +
            '<div class="panel-card__header">' +
                '<h2><i class="fas fa-box-open"></i> E\'lonlarim (' + (products ? products.length : 0) + ')</h2>' +
                '<button class="btn btn-primary btn-sm" onclick="sellerShowAddProduct()">' +
                    '<i class="fas fa-plus"></i> Yangi e\'lon' +
                '</button>' +
            '</div>' +
            '<div class="panel-card__body">';

        if (!products || !products.length) {
            html += '<div class="empty-state">' +
                '<i class="fas fa-bullhorn"></i>' +
                '<p>Hali e\'lon joylamagan ekansiz</p>' +
                '<button class="btn btn-primary" onclick="sellerShowAddProduct()" style="margin-top:12px">' +
                '<i class="fas fa-plus"></i> Birinchi e\'lon</button>' +
            '</div>';
        } else {
            html += '<div class="orders-list">';
            products.forEach(function (p) {
                var img = (p.images && p.images.length) ? p.images[0] : null;
                var imgTag = img
                    ? '<img class="order-card__img" src="' + imageUrl(img.image) + '">'
                    : '<div class="order-card__img" style="display:flex;align-items:center;justify-content:center;background:var(--bg)"><i class="fas fa-image"></i></div>';

                var actionBtns = "";
                if (p.status === "moderation") {
                    actionBtns += '<span class="badge badge-warning" style="font-size:.8rem;padding:4px 10px"><i class="fas fa-clock"></i> Moderatsiyada</span>';
                }
                if (p.status === "active") {
                    actionBtns += '<button class="btn btn-outline btn-sm" onclick="archiveProduct(' + p.id + ')"><i class="fas fa-archive"></i> Arxiv</button>';
                    actionBtns += '<button class="btn btn-primary btn-sm" onclick="markSold(' + p.id + ')" style="margin-left:4px"><i class="fas fa-check-double"></i> Sotildi</button>';
                }
                if (p.status !== "sold") {
                    actionBtns += '<button class="btn btn-warning btn-sm" onclick="showEditProductModal(' + p.id + ')" style="margin-left:4px"><i class="fas fa-edit"></i> Tahrirlash</button>';
                }
                actionBtns += '<button class="btn btn-danger btn-sm" onclick="confirmDeleteProduct(' + p.id + ', \'' + escHtml(p.title).replace(/'/g, "\\'") + '\')" style="margin-left:4px"><i class="fas fa-trash"></i></button>';

                html += '<div class="order-card">' +
                    imgTag +
                    '<div class="order-card__info">' +
                        '<div class="order-card__title">' + escHtml(p.title) + '</div>' +
                        '<div class="order-card__meta">' +
                            statusBadge(p.status) + ' · ' +
                            formatPrice(p.price_with_tax || p.price) + " so'm · " +
                            '<i class="fas fa-eye"></i> ' + p.view_count + ' · ' +
                            new Date(p.created_at).toLocaleDateString("uz-UZ") +
                        '</div>' +
                    '</div>' +
                    '<div class="order-card__actions">' + actionBtns + '</div>' +
                '</div>';
            });
            html += '</div>';
        }

        html += '</div></div>';
        content.innerHTML = html;

    } catch (e) {
        console.error("Mahsulotlar yuklanmadi:", e);
        content.innerHTML =
            '<div class="empty-state">' +
                '<i class="fas fa-exclamation-triangle"></i>' +
                '<p>Mahsulotlar yuklanmadi. Avval sotuvchi profilini yarating.</p>' +
            '</div>';
    }
}

// ═══════════════ ADD PRODUCT (open modal) ═══════════════
function sellerShowAddProduct() {
    setSellerNav("add-product");
    // Open the existing add product modal from app.js
    showAddProductModal();
}

// ═══════════════ ORDERS ═══════════════
async function sellerShowOrders() {
    setSellerNav("orders");
    setSellerTopbar("Buyurtmalar", "Sizga kelgan buyurtmalar");

    var content = document.getElementById("sellerContent");
    content.innerHTML = '<div class="loader"><div class="spinner"></div></div>';

    try {
        var orders = await api.get("/orders/?role=seller");

        var html = '<div class="panel-card">' +
            '<div class="panel-card__header">' +
                '<h2><i class="fas fa-shopping-bag"></i> Buyurtmalar (' + orders.length + ')</h2>' +
                '<button class="btn btn-outline btn-sm" onclick="sellerShowOrders()" style="margin-left:auto">' +
                    '<i class="fas fa-sync-alt"></i> Yangilash' +
                '</button>' +
            '</div>' +
            '<div class="panel-card__body">';

        if (!orders || !orders.length) {
            html += '<div class="empty-state">' +
                '<i class="fas fa-inbox"></i>' +
                '<p>Hali buyurtma yo\'q</p>' +
            '</div>';
        } else {
            html += '<div class="orders-list">';
            orders.forEach(function (order) {
                var productTitle = order.product_title || ("Mahsulot #" + order.product);
                var buyerName = order.buyer_full_name || order.buyer_username || ("Haridor #" + order.buyer);
                
                // Haridor manzili
                var addressHtml = "";
                if (order.buyer_address) {
                    addressHtml = '<div class="order-address">' +
                        '<i class="fas fa-map-marker-alt"></i> ' +
                        escHtml(order.buyer_address.full || order.buyer_address.address) +
                    '</div>';
                }

                // Status badge ranglari
                var statusClass = {
                    'pending': 'warning',
                    'agreed': 'info',
                    'completed': 'success',
                    'canceled': 'danger'
                };

                var actionBtns = "";
                if (order.status === "pending") {
                    actionBtns =
                        '<button class="btn btn-success btn-sm" onclick="sellerUpdateOrder(' + order.id + ', \'agreed\')">' +
                            '<i class="fas fa-check"></i> Qabul qilish' +
                        '</button>' +
                        '<button class="btn btn-danger btn-sm" onclick="sellerUpdateOrder(' + order.id + ', \'canceled\')" style="margin-left:4px">' +
                            '<i class="fas fa-times"></i> Rad etish' +
                        '</button>';
                } else if (order.status === "agreed") {
                    actionBtns = '<span class="badge badge-info"><i class="fas fa-clock"></i> Haridor tasdiqlashini kutmoqda</span>';
                } else if (order.status === "completed") {
                    actionBtns = '<span class="badge badge-success"><i class="fas fa-check-double"></i> Yakunlangan</span>';
                } else if (order.status === "canceled") {
                    actionBtns = '<span class="badge badge-danger"><i class="fas fa-ban"></i> Bekor qilingan</span>';
                }

                // Rasm
                var imgHtml = '';
                if (order.product_image) {
                    imgHtml = '<img class="order-card__img" src="' + imageUrl(order.product_image) + '" style="width:60px;height:60px;object-fit:cover;border-radius:8px;margin-right:12px">';
                }

                html += '<div class="order-card" style="padding:16px;border:1px solid var(--border);border-radius:12px;margin-bottom:12px">' +
                    '<div style="display:flex;align-items:flex-start">' +
                        imgHtml +
                        '<div class="order-card__info" style="flex:1">' +
                            '<div class="order-card__title" style="font-weight:600;font-size:1rem;margin-bottom:4px">' +
                                escHtml(productTitle) +
                            '</div>' +
                            '<div class="order-card__meta" style="font-size:.85rem;color:var(--text-secondary);margin-bottom:8px">' +
                                '<span style="margin-right:12px">' + statusBadge(order.status) + '</span>' +
                                '<span><i class="fas fa-money-bill"></i> ' + formatPrice(order.final_price) + " so'm</span>" +
                            '</div>' +
                            '<div style="font-size:.85rem;margin-bottom:4px">' +
                                '<i class="fas fa-user"></i> <strong>Haridor:</strong> ' + escHtml(buyerName) +
                            '</div>' +
                            addressHtml +
                            '<div style="font-size:.8rem;color:var(--text-secondary);margin-top:4px">' +
                                '<i class="fas fa-calendar"></i> ' + new Date(order.created_at).toLocaleString("uz-UZ") +
                            '</div>' +
                            (order.notes ? '<div style="font-size:.8rem;color:var(--text-secondary);margin-top:4px"><i class="fas fa-sticky-note"></i> ' + escHtml(order.notes) + '</div>' : '') +
                        '</div>' +
                    '</div>' +
                    '<div class="order-card__actions" style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border)">' +
                        actionBtns +
                    '</div>' +
                '</div>';
            });
            html += '</div>';
        }

        html += '</div></div>';
        content.innerHTML = html;

    } catch (e) {
        console.error("Buyurtmalar yuklanmadi:", e);
        content.innerHTML =
            '<div class="empty-state">' +
                '<i class="fas fa-exclamation-triangle"></i>' +
                '<p>Buyurtmalar yuklanmadi</p>' +
            '</div>';
    }
}

async function sellerUpdateOrder(orderId, newStatus) {
    try {
        var body = { status: newStatus };
        var res = await api.patch("/orders/" + orderId + "/", body);
        var data = await res.json();
        if (res.ok) {
            toast("Buyurtma yangilandi!", "success");
            sellerShowOrders();
        } else {
            toast(data.detail || "Xatolik", "error");
        }
    } catch (e) {
        toast("Xatolik yuz berdi", "error");
    }
}

// ═══════════════ PROFILE ═══════════════
async function sellerShowProfile() {
    setSellerNav("profile");
    setSellerTopbar("Profil", "Shaxsiy va do'kon ma'lumotlari");

    var content = document.getElementById("sellerContent");
    content.innerHTML = '<div class="loader"><div class="spinner"></div></div>';

    try {
        var avatar = currentUser.username ? currentUser.username[0].toUpperCase() : "S";

        var html = '<div class="panel-card" style="margin-bottom:20px">' +
            '<div class="panel-card__header"><h2><i class="fas fa-user"></i> Foydalanuvchi ma\'lumotlari</h2></div>' +
            '<div class="panel-card__body">' +
                '<div style="display:flex;align-items:center;gap:16px;margin-bottom:20px">' +
                    '<div class="seller-topbar__avatar" style="width:64px;height:64px;font-size:1.5rem">' + avatar + '</div>' +
                    '<div>' +
                        '<h3 style="margin:0">' + escHtml(currentUser.username) + '</h3>' +
                        '<p style="margin:4px 0 0;color:var(--text-secondary)">' + escHtml(currentUser.email || "") + '</p>' +
                        '<span class="status-badge status-active" style="margin-top:6px;display:inline-block">Sotuvchi</span>' +
                    '</div>' +
                '</div>' +
            '</div>' +
        '</div>';

        // Do'kon info
        try {
            var sellerRes = await api.get("/sellers/" + currentUser.id + "/");
            var s = sellerRes.seller;

            html += '<div class="panel-card" style="margin-bottom:20px">' +
                '<div class="panel-card__header"><h2><i class="fas fa-store"></i> Do\'kon profili</h2></div>' +
                '<div class="panel-card__body">' +
                    '<dl class="detail-specs">' +
                        '<dt>Do\'kon nomi</dt><dd>' + escHtml(s.shop_name || "—") + '</dd>' +
                        '<dt>Reyting</dt><dd>' + starsHtml(s.rating || 0) + ' (' + (s.rating || 0).toFixed(1) + ')</dd>' +
                        '<dt>Jami sotilgan</dt><dd>' + (s.total_sales || 0) + ' ta</dd>' +
                        (s.region ? '<dt>Viloyat</dt><dd>' + escHtml(s.region) + '</dd>' : '') +
                        (s.district ? '<dt>Tuman</dt><dd>' + escHtml(s.district) + '</dd>' : '') +
                        (s.adress ? '<dt>Manzil</dt><dd>' + escHtml(s.adress) + '</dd>' : '') +
                        (s.shop_description ? '<dt>Tavsif</dt><dd>' + escHtml(s.shop_description) + '</dd>' : '') +
                    '</dl>' +
                '</div>' +
            '</div>';

            // Logo
            if (s.shop_logo) {
                html += '<div class="panel-card" style="margin-bottom:20px">' +
                    '<div class="panel-card__header"><h2><i class="fas fa-image"></i> Do\'kon logosi</h2></div>' +
                    '<div class="panel-card__body" style="text-align:center">' +
                        '<img src="' + imageUrl(s.shop_logo) + '" style="max-width:200px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,.1)">' +
                    '</div>' +
                '</div>';
            }
        } catch (e) {
            html += '<div class="panel-card" style="margin-bottom:20px;border-left:4px solid var(--warning)">' +
                '<div class="panel-card__body" style="display:flex;align-items:center;gap:12px">' +
                    '<i class="fas fa-info-circle" style="font-size:1.3rem;color:var(--warning)"></i>' +
                    '<p style="margin:0;font-size:.9rem">Sotuvchi profili hali yaratilmagan. Admin bilan bog\'laning.</p>' +
                '</div>' +
            '</div>';
        }

        // Logout
        html += '<button class="btn btn-danger" onclick="handleLogout()" style="margin-top:8px">' +
            '<i class="fas fa-sign-out-alt"></i> Tizimdan chiqish</button>';

        content.innerHTML = html;

    } catch (e) {
        console.error("Profil yuklanmadi:", e);
        content.innerHTML =
            '<div class="empty-state">' +
                '<i class="fas fa-exclamation-triangle"></i>' +
                '<p>Profil yuklanmadi</p>' +
            '</div>';
    }
}

// ═══════════════ OVERRIDES ═══════════════
// Override goHome so it works within seller panel context
// After adding a product via modal, redirect to seller products
(function () {
    // Save original showMyProducts for the modal callbacks
    var _origShowMyProducts = typeof showMyProducts === "function" ? showMyProducts : null;

    // Override showMyProducts to use sellerShowProducts in seller panel
    window.showMyProducts = function () {
        sellerShowProducts();
    };

    // Override goHome for seller context
    window.goHome = function () {
        sellerGoHome();
    };
})();

// ═══════════════ AUTH UI OVERRIDE ═══════════════
// On seller page, auth UI elements may not exist — stub them out
(function () {
    var _origUpdateAuthUI = typeof updateAuthUI === "function" ? updateAuthUI : null;
    window.updateAuthUI = function () {
        // Only update elements that exist on this page
        var loginBtn = document.getElementById("loginBtn");
        var profileBtn = document.getElementById("profileBtn");
        var favoritesBtn = document.getElementById("favoritesBtn");
        var ordersBtn = document.getElementById("ordersBtn");
        var myProductsBtn = document.getElementById("myProductsBtn");
        var fabAdd = document.getElementById("fabAdd");

        var logged = isLoggedIn();

        if (loginBtn) loginBtn.style.display = logged ? "none" : "flex";
        if (profileBtn) profileBtn.style.display = logged ? "flex" : "none";
        if (favoritesBtn) favoritesBtn.style.display = logged ? "flex" : "none";
        if (ordersBtn) ordersBtn.style.display = logged ? "flex" : "none";
        if (myProductsBtn) {
            var isSeller = logged && currentUser && currentUser.role === "seller";
            myProductsBtn.style.display = isSeller ? "flex" : "none";
        }
        if (fabAdd) {
            var isSeller = logged && currentUser && currentUser.role === "seller";
            fabAdd.style.display = isSeller ? "flex" : "none";
        }

        if (logged && currentUser) {
            var profileName = document.getElementById("profileName");
            if (profileName) profileName.textContent = currentUser.username || "Profil";
        }
    };
})();
