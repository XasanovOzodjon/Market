/* ═══════════════════════════════════════════
   APP.JS — Market Frontend Main Logic
   ═══════════════════════════════════════════ */

var categoriesCache = [];
var brandsCache = [];
var activeCategory = null;
var searchTimeout = null;

// ═══════════════ INIT ═══════════════
document.addEventListener("DOMContentLoaded", function () {
    checkGoogleCallback();
    updateAuthUI();
    fetchCurrentUser();

    // Skip index.html-specific init on seller page
    if (document.getElementById("sellerContent")) return;

    loadCategories();
    loadProducts();
    setupPricePreview();
});

// ═══════════════ KATEGORIYALAR ═══════════════
async function loadCategories() {
    try {
        categoriesCache = await api.get("/categories/");
        renderCategoryList();
    } catch (e) {
        console.error("Kategoriyalar yuklanmadi:", e);
    }
}

function renderCategoryList() {
    var list = document.getElementById("categoryList");
    if (!list) return; // Element mavjud bo'lmasa (seller.html da yo'q)

    var html = '<li class="' + (!activeCategory ? "active" : "") + '" onclick="filterByCategory(null)">' +
        '<i class="fas fa-th-large"></i> Barchasi</li>';

    categoriesCache.forEach(function (cat) {
        var isActive = activeCategory && activeCategory === cat.slug;
        html += '<li class="' + (isActive ? "active" : "") + '" onclick="filterByCategory(\'' + cat.slug + '\')">' +
            '<i class="fas ' + categoryIcon(cat.category_type) + '"></i> ' + escHtml(cat.name) + '</li>';
    });

    list.innerHTML = html;
}

function filterByCategory(slug) {
    activeCategory = slug;
    renderCategoryList();
    loadProducts();
}

// ═══════════════ MAHSULOTLAR ═══════════════
async function loadProducts(url) {
    var content = document.getElementById("content");
    if (!content) return;
    content.innerHTML = '<div class="loader"><div class="spinner"></div></div>';

    try {
        var endpoint = url || buildProductsUrl();
        var data = await api.get(endpoint);

        var products = data.results || data;
        var html = renderProductsGrid(products);

        if (data.results) {
            html += renderPagination(data);
        }

        content.innerHTML = html;
    } catch (e) {
        console.error("Mahsulotlar yuklanmadi:", e);
        content.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i>' +
            '<p>Xatolik yuz berdi</p></div>';
    }
}

function buildProductsUrl() {
    var params = [];

    if (activeCategory) {
        return "/categories/" + activeCategory + "/products/";
    }

    var minP = document.getElementById("filterMinPrice").value;
    var maxP = document.getElementById("filterMaxPrice").value;
    var order = document.getElementById("filterOrdering").value;
    var search = document.getElementById("searchInput").value.trim();

    if (minP) params.push("min_price=" + minP);
    if (maxP) params.push("max_price=" + maxP);
    if (order) params.push("ordering=" + order);
    if (search) params.push("search=" + encodeURIComponent(search));

    return "/products/" + (params.length ? "?" + params.join("&") : "");
}

function loadPage(url) {
    loadProducts(url);
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function applyFilters() {
    activeCategory = null;
    renderCategoryList();
    loadProducts();
}

function resetFilters() {
    document.getElementById("filterMinPrice").value = "";
    document.getElementById("filterMaxPrice").value = "";
    document.getElementById("filterOrdering").value = "-created_at";
    document.getElementById("searchInput").value = "";
    activeCategory = null;
    renderCategoryList();
    loadProducts();
}

function handleSearch(event) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(function () {
        activeCategory = null;
        renderCategoryList();
        loadProducts();
    }, 500);
}

function goHome() {
    resetFilters();
}

// ═══════════════ MAHSULOT BATAFSIL ═══════════════
async function showProductDetail(id) {
    var content = document.getElementById("content");
    content.innerHTML = '<div class="loader"><div class="spinner"></div></div>';

    try {
        var p = await api.get("/products/" + id + "/");
        renderProductDetail(p);
    } catch (e) {
        console.error("Mahsulot yuklanmadi:", e);
        content.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Mahsulot topilmadi</p></div>';
    }
}

function renderProductDetail(p) {
    var content = document.getElementById("content");

    // Rasmlar
    var images = p.images || [];
    var mainImg = images.find(function (i) { return i.is_main; }) || images[0];
    var mainSrc = mainImg ? imageUrl(mainImg.image) : "";

    var galleryHtml = "";
    if (mainSrc) {
        galleryHtml = '<img class="product-detail__main-img" id="detailMainImg" src="' + mainSrc + '" alt="' + escHtml(p.title) + '">';
        if (images.length > 1) {
            galleryHtml += '<div class="product-detail__thumbs">';
            images.forEach(function (img, idx) {
                var cls = (mainImg && img.id === mainImg.id) ? "active" : "";
                galleryHtml += '<img class="product-detail__thumb ' + cls + '" src="' + imageUrl(img.image) +
                    '" onclick="changeMainImage(this, \'' + imageUrl(img.image) + '\')">';
            });
            galleryHtml += '</div>';
        }
    } else {
        galleryHtml = '<div class="product-card__img-placeholder" style="height:400px"><i class="fas fa-image"></i></div>';
    }

    // Narx bloki
    var displayPrice = p.price_with_tax || p.price;
    var hasTax = p.tax_percent && parseFloat(p.tax_percent) > 0;

    var taxHtml = "";
    if (hasTax) {
        taxHtml = '<div class="price-block__tax">' +
            '<span>Asosiy narx: <strong>' + formatPrice(p.price) + " so'm</strong></span>" +
            '<span>Soliq (' + p.tax_percent + '%): <strong>+' + formatPrice(p.tax_amount) + " so'm</strong></span>" +
        '</div>';
    }

    // Atribut specs
    var specsHtml = renderAttributeSpecs(p);

    // Brand
    var brandHtml = "";
    if (p.brand) {
        brandHtml = "<dt>Brend</dt><dd>" + escHtml(p.brand.name) + "</dd>";
    }

    // Seller
    var sellerInitial = "S";
    var sellerName = "Sotuvchi #" + p.seller;
    var sellerClick = 'onclick="showSellerProfile(' + p.seller + ')"';

    // Haridor uchun tugma
    var buyBtn = "";
    if (isLoggedIn() && currentUser && currentUser.id !== p.seller) {
        buyBtn = '<button class="btn btn-success" onclick="createOrder(' + p.id + ')">' +
            '<i class="fas fa-shopping-cart"></i> Buyurtma berish</button>';
    }

    var favBtn = "";
    if (isLoggedIn()) {
        favBtn = '<button class="btn btn-outline" onclick="toggleFavorite(' + p.id + ')">' +
            '<i class="fas fa-heart"></i> Sevimlilarga</button>';
    }

    content.innerHTML =
        '<button class="back-btn" onclick="goHome()"><i class="fas fa-arrow-left"></i> Orqaga</button>' +
        '<div class="product-detail">' +
            '<div class="product-detail__gallery">' + galleryHtml + '</div>' +
            '<div class="product-detail__info">' +
                '<h1>' + escHtml(p.title) + '</h1>' +
                '<span class="category-tag"><i class="fas fa-tag"></i> Kategoriya</span> ' +
                '<div class="price-block">' +
                    '<div class="price-block__main">' + formatPrice(displayPrice) + " so'm</div>" +
                    taxHtml +
                '</div>' +
                '<dl class="detail-specs">' +
                    brandHtml + specsHtml +
                    '<dt>Ko\'rishlar</dt><dd>' + p.view_count + '</dd>' +
                    '<dt>E\'lon sanasi</dt><dd>' + new Date(p.created_at).toLocaleDateString("uz-UZ") + '</dd>' +
                '</dl>' +
                '<div class="seller-card" ' + sellerClick + '>' +
                    '<div class="seller-card__avatar">' + sellerInitial + '</div>' +
                    '<div><div class="seller-card__name">' + sellerName + '</div>' +
                    '<div class="seller-card__rating"><i class="fas fa-store"></i> Sotuvchi profilini ko\'rish</div></div>' +
                '</div>' +
                '<div class="detail-actions">' + buyBtn + favBtn + '</div>' +
            '</div>' +
            '<div class="product-detail__description">' +
                '<h3><i class="fas fa-align-left"></i> Tavsif</h3>' +
                '<p>' + escHtml(p.description) + '</p>' +
            '</div>' +
        '</div>';
}

function changeMainImage(thumbEl, src) {
    document.getElementById("detailMainImg").src = src;
    document.querySelectorAll(".product-detail__thumb").forEach(function (el) {
        el.classList.remove("active");
    });
    thumbEl.classList.add("active");
}

// ═══════════════ SOTUVCHI PROFILI ═══════════════
async function showSellerProfile(sellerId) {
    var content = document.getElementById("content");
    content.innerHTML = '<div class="loader"><div class="spinner"></div></div>';

    try {
        var sellerRes = await api.get("/sellers/" + sellerId + "/");
        var seller = sellerRes.seller;
        var prodsRes = await api.get("/sellers/" + sellerId + "/products/");
        var products = prodsRes.products || prodsRes;

        var logoHtml = seller.shop_logo
            ? '<img class="seller-page__logo" src="' + imageUrl(seller.shop_logo) + '">'
            : '<div class="seller-card__avatar" style="width:80px;height:80px;font-size:2rem">' +
              (seller.shop_name ? seller.shop_name[0].toUpperCase() : "S") + '</div>';

        var html =
            '<button class="back-btn" onclick="goHome()"><i class="fas fa-arrow-left"></i> Orqaga</button>' +
            '<div class="seller-page__header">' +
                logoHtml +
                '<div>' +
                    '<div class="seller-page__name">' + escHtml(seller.shop_name) + '</div>' +
                    '<div class="seller-page__meta">' +
                        '<span><i class="fas fa-star" style="color:var(--warning)"></i> ' + (seller.rating || 0).toFixed(1) + '</span> · ' +
                        '<span><i class="fas fa-box"></i> ' + (seller.total_sales || 0) + ' ta sotilgan</span> · ' +
                        '<span><i class="fas fa-map-marker-alt"></i> ' + escHtml(seller.region || "") + '</span>' +
                    '</div>' +
                    (seller.shop_description ? '<p style="margin-top:8px;font-size:.9rem;color:var(--text-secondary)">' + escHtml(seller.shop_description) + '</p>' : '') +
                '</div>' +
            '</div>' +
            '<h3 style="margin-bottom:16px"><i class="fas fa-box-open"></i> Mahsulotlari</h3>' +
            renderProductsGrid(products);

        content.innerHTML = html;

        // Reviews
        loadSellerReviews(sellerId, content);

    } catch (e) {
        console.error("Seller yuklanmadi:", e);
        content.innerHTML = '<button class="back-btn" onclick="goHome()"><i class="fas fa-arrow-left"></i> Orqaga</button>' +
            '<div class="empty-state"><i class="fas fa-user-slash"></i><p>Sotuvchi topilmadi</p></div>';
    }
}

async function loadSellerReviews(sellerId, container) {
    try {
        var reviews = await api.get("/reviews/?seller_id=" + sellerId);
        if (reviews && reviews.length) {
            var html = '<div style="margin-top:32px">' +
                '<h3><i class="fas fa-comments"></i> Sharhlar (' + reviews.length + ')</h3>' +
                '<div class="reviews-list">';

            reviews.forEach(function (r) {
                html += '<div class="review-card">' +
                    '<div class="review-card__header">' +
                        '<span class="review-card__stars">' + starsHtml(r.rating) + '</span>' +
                        '<span class="review-card__date">' + new Date(r.created_at).toLocaleDateString("uz-UZ") + '</span>' +
                    '</div>' +
                    (r.comment ? '<div class="review-card__text">' + escHtml(r.comment) + '</div>' : '') +
                '</div>';
            });

            html += '</div></div>';
            container.innerHTML += html;
        }
    } catch (e) {
        console.error("Sharhlar yuklanmadi:", e);
    }
}

// ═══════════════ SEVIMLILAR ═══════════════
async function showFavorites() {
    if (!isLoggedIn()) { showAuthModal(); return; }

    var content = document.getElementById("content");
    content.innerHTML = '<div class="loader"><div class="spinner"></div></div>';

    try {
        var favs = await api.get("/favorites/");
        if (!favs || !favs.length) {
            content.innerHTML = '<button class="back-btn" onclick="goHome()"><i class="fas fa-arrow-left"></i> Orqaga</button>' +
                '<div class="empty-state"><i class="fas fa-heart"></i><p>Sevimlilar bo\'sh</p></div>';
            return;
        }

        // Har bir favorite dan product ma'lumotlarini olish
        var html = '<button class="back-btn" onclick="goHome()"><i class="fas fa-arrow-left"></i> Orqaga</button>' +
            '<h2 style="margin-bottom:16px"><i class="fas fa-heart" style="color:var(--danger)"></i> Sevimlilar</h2>' +
            '<div class="orders-list">';

        for (var i = 0; i < favs.length; i++) {
            var fav = favs[i];
            var pd = fav.product_detail;
            var favTitle = pd ? escHtml(pd.title) : ("Mahsulot #" + fav.product);
            var favPrice = pd ? formatPrice(pd.price_with_tax || pd.price) + " so'm" : "";
            var favImg = "";
            if (pd && pd.images && pd.images.length) {
                var mainImg = pd.images.find(function(im) { return im.is_main; }) || pd.images[0];
                favImg = '<img class="order-card__img" src="' + imageUrl(mainImg.image) + '" style="width:64px;height:64px;object-fit:cover;border-radius:8px;margin-right:12px">';
            }
            var productId = pd ? pd.id : fav.product;
            html += '<div class="order-card">' +
                favImg +
                '<div class="order-card__info">' +
                    '<div class="order-card__title" style="cursor:pointer" onclick="showProductDetail(' + productId + ')">' + favTitle + '</div>' +
                    '<div class="order-card__meta">' + favPrice + (favPrice ? ' · ' : '') + new Date(fav.created_at).toLocaleDateString("uz-UZ") + '</div>' +
                '</div>' +
                '<div class="order-card__actions">' +
                    '<button class="btn btn-danger btn-sm" onclick="removeFavorite(' + fav.id + ')"><i class="fas fa-trash"></i> O\'chirish</button>' +
                '</div>' +
            '</div>';
        }

        html += '</div>';
        content.innerHTML = html;

    } catch (e) {
        console.error("Sevimlilar yuklanmadi:", e);
    }
}

async function toggleFavorite(productId) {
    if (!isLoggedIn()) { showAuthModal(); return; }
    try {
        var res = await api.post("/favorites/", { product_id: productId });
        var data = await res.json();
        if (res.ok) {
            toast("Sevimlilarga qo'shildi!", "success");
        } else {
            toast(data.detail || "Xatolik", "error");
        }
    } catch (e) {
        toast("Xatolik yuz berdi", "error");
    }
}

async function removeFavorite(favId) {
    try {
        await api.delete("/favorites/" + favId + "/");
        toast("Sevimlilardan o'chirildi", "info");
        showFavorites();
    } catch (e) {
        toast("Xatolik yuz berdi", "error");
    }
}

// ═══════════════ BUYURTMALAR ═══════════════
async function showOrders() {
    if (!isLoggedIn()) { showAuthModal(); return; }

    var content = document.getElementById("content");
    content.innerHTML = '<div class="loader"><div class="spinner"></div></div>';

    try {
        var orders = await api.get("/orders/");

        if (!orders || !orders.length) {
            content.innerHTML = '<button class="back-btn" onclick="goHome()"><i class="fas fa-arrow-left"></i> Orqaga</button>' +
                '<div class="empty-state"><i class="fas fa-box"></i><p>Buyurtmalar yo\'q</p></div>';
            return;
        }

        var html = '<button class="back-btn" onclick="goHome()"><i class="fas fa-arrow-left"></i> Orqaga</button>' +
            '<h2 style="margin-bottom:16px"><i class="fas fa-box"></i> Buyurtmalar</h2>' +
            '<div class="orders-list">';

        orders.forEach(function (order) {
            var isBuyer = currentUser && order.buyer === currentUser.id;
            var isSeller = currentUser && order.seller === currentUser.id;
            var roleTag = isBuyer ? "Haridor" : "Sotuvchi";
            var otherUser = isBuyer ? (order.seller_username || "Sotuvchi") : (order.buyer_full_name || order.buyer_username || "Haridor");
            var productTitle = order.product_title || ("Mahsulot #" + order.product);

            var orderImg = "";
            if (order.product_image) {
                orderImg = '<img src="' + imageUrl(order.product_image) + '" style="width:56px;height:56px;object-fit:cover;border-radius:8px;margin-right:12px">';
            }

            // Manzil (faqat sotuvchi ko'radi)
            var addressHtml = "";
            if (isSeller && order.buyer_address) {
                addressHtml = '<div class="order-address"><i class="fas fa-map-marker-alt"></i> ' + 
                    escHtml(order.buyer_address.full || order.buyer_address.address) + '</div>';
            }

            var actionBtns = "";

            // Seller: pending → agree / cancel
            if (isSeller && order.status === "pending") {
                actionBtns =
                    '<button class="btn btn-success btn-sm" onclick="updateOrder(' + order.id + ', \'agreed\')"><i class="fas fa-check"></i> Qabul</button>' +
                    '<button class="btn btn-danger btn-sm" onclick="updateOrder(' + order.id + ', \'canceled\')"><i class="fas fa-times"></i> Rad</button>';
            }

            // Buyer: agreed → complete / cancel
            if (isBuyer && order.status === "agreed") {
                actionBtns =
                    '<button class="btn btn-success btn-sm" onclick="updateOrder(' + order.id + ', \'completed\')"><i class="fas fa-check-double"></i> Sotib oldim</button>' +
                    '<button class="btn btn-danger btn-sm" onclick="updateOrder(' + order.id + ', \'canceled\')"><i class="fas fa-times"></i> Bekor</button>';
            }

            // Buyer: pending → cancel
            if (isBuyer && order.status === "pending") {
                actionBtns =
                    '<span class="badge badge-warning"><i class="fas fa-clock"></i> Sotuvchi javobini kutmoqda</span>' +
                    '<button class="btn btn-danger btn-sm" onclick="updateOrder(' + order.id + ', \'canceled\')" style="margin-left:8px"><i class="fas fa-times"></i> Bekor</button>';
            }

            // Buyer: completed & no review → write review
            if (isBuyer && order.status === "completed") {
                actionBtns += '<button class="btn btn-primary btn-sm" onclick="showReviewForm(' + order.id + ')"><i class="fas fa-pen"></i> Sharh yozish</button>';
            }

            html += '<div class="order-card" style="padding:16px;border:1px solid var(--border);border-radius:12px;margin-bottom:12px">' +
                '<div style="display:flex;align-items:flex-start">' +
                    orderImg +
                    '<div class="order-card__info" style="flex:1">' +
                        '<div class="order-card__title" style="cursor:pointer;font-weight:600" onclick="showProductDetail(' + (order.product_id || order.product) + ')">' +
                            escHtml(productTitle) + ' <small style="color:var(--text-secondary)">(#' + order.id + ')</small>' +
                        '</div>' +
                        '<div class="order-card__meta" style="margin-top:6px;font-size:.85rem">' +
                            '<span style="margin-right:8px">' + statusBadge(order.status) + '</span>' +
                            '<span><i class="fas fa-money-bill"></i> ' + formatPrice(order.final_price) + " so'm</span> · " +
                            '<span><i class="fas fa-user"></i> ' + roleTag + '</span> · ' +
                            '<span><i class="fas fa-calendar"></i> ' + new Date(order.created_at).toLocaleDateString("uz-UZ") + '</span>' +
                        '</div>' +
                        (isSeller ? '<div style="font-size:.85rem;margin-top:6px"><i class="fas fa-user"></i> Haridor: <strong>' + escHtml(otherUser) + '</strong></div>' : '') +
                        (isBuyer && order.seller_shop_name ? '<div style="font-size:.85rem;margin-top:6px"><i class="fas fa-store"></i> Sotuvchi: <strong>' + escHtml(order.seller_shop_name) + '</strong></div>' : '') +
                        addressHtml +
                        (order.notes ? '<div style="font-size:.8rem;color:var(--text-secondary);margin-top:4px"><i class="fas fa-sticky-note"></i> ' + escHtml(order.notes) + '</div>' : '') +
                    '</div>' +
                '</div>' +
                '<div class="order-card__actions" style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border)">' + actionBtns + '</div>' +
            '</div>';
        });

        html += '</div>';
        content.innerHTML = html;

    } catch (e) {
        console.error("Buyurtmalar yuklanmadi:", e);
    }
}

// ═══════════════ BUYURTMA YARATISH (MODAL) ═══════════════
var orderProductId = null;
var savedUserAddress = null;
var isOrderSubmitting = false; // Takroriy yuborishni oldini olish

// Order modalni yopish
function closeOrderModal(event) {
    // Agar event bor bo'lsa va modal ichiga bosilgan bo'lsa, yopmaslik
    if (event && event.target.id !== 'orderModal') {
        return;
    }
    
    var modal = document.getElementById('orderModal');
    if (modal) {
        modal.remove();
        document.body.style.overflow = "";
        // Global o'zgaruvchilarni tozalash
        orderProductId = null;
        isOrderSubmitting = false;
        console.log("Order modal yopildi");
    }
}

async function showOrderModal(productId) {
    if (!isLoggedIn()) { showAuthModal(); return; }
    
    // Agar modal allaqachon ochiq bo'lsa, qaytadan ochmang
    if (document.getElementById('orderModal')) {
        return;
    }
    
    orderProductId = productId;
    isOrderSubmitting = false;
    
    // Mavjud manzilni olish
    try {
        savedUserAddress = await api.get("/address/");
    } catch (e) {
        savedUserAddress = null;
    }
    
    var hasAddress = savedUserAddress && savedUserAddress.address;
    
    var modalHtml = 
        '<div class="modal-overlay" id="orderModal" style="display:flex" onclick="closeOrderModal(event)">' +
            '<div class="modal" style="max-width:500px" onclick="event.stopPropagation()">' +
                '<button class="modal-close" onclick="closeOrderModal()">&times;</button>' +
                '<h2><i class="fas fa-shopping-cart"></i> Buyurtma berish</h2>' +
                '<form id="orderForm" onsubmit="submitOrder(event)">' +
                    '<div class="form-group">' +
                        '<label>Yetkazib berish manzili</label>' +
                        (hasAddress ? 
                            '<div class="address-options">' +
                                '<label class="radio-option">' +
                                    '<input type="radio" name="addressOption" value="saved" checked onchange="toggleAddressFields()">' +
                                    '<span>Saqlangan manzil: <strong>' + escHtml(savedUserAddress.address) + ', ' + escHtml(savedUserAddress.city) + '</strong></span>' +
                                '</label>' +
                                '<label class="radio-option">' +
                                    '<input type="radio" name="addressOption" value="new" onchange="toggleAddressFields()">' +
                                    '<span>Yangi manzil kiritish</span>' +
                                '</label>' +
                            '</div>' 
                        : '') +
                    '</div>' +
                    '<div id="newAddressFields" style="' + (hasAddress ? 'display:none' : '') + '">' +
                        '<div class="form-group">' +
                            '<label>Manzil *</label>' +
                            '<input type="text" id="orderAddress" placeholder="Ko\'cha, uy raqami...">' +
                        '</div>' +
                        '<div class="form-row">' +
                            '<div class="form-group">' +
                                '<label>Shahar *</label>' +
                                '<input type="text" id="orderCity" placeholder="Shahar nomi">' +
                            '</div>' +
                            '<div class="form-group">' +
                                '<label>Mamlakat *</label>' +
                                '<input type="text" id="orderCountry" value="O\'zbekiston">' +
                            '</div>' +
                        '</div>' +
                        '<div class="form-group">' +
                            '<label>Pochta indeksi *</label>' +
                            '<input type="text" id="orderPostalCode" placeholder="100000">' +
                        '</div>' +
                    '</div>' +
                    '<div class="form-group">' +
                        '<label>Izoh (ixtiyoriy)</label>' +
                        '<textarea id="orderNotes" rows="2" placeholder="Qo\'shimcha ma\'lumotlar..."></textarea>' +
                    '</div>' +
                    '<button type="submit" class="btn btn-success btn-block" id="orderSubmitBtn">' +
                        '<i class="fas fa-check"></i> Buyurtma berish' +
                    '</button>' +
                '</form>' +
            '</div>' +
        '</div>';
    
    // Modal qo'shish
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    document.body.style.overflow = "hidden";
}

function toggleAddressFields() {
    var option = document.querySelector('input[name="addressOption"]:checked');
    var fields = document.getElementById('newAddressFields');
    if (option && option.value === 'new') {
        fields.style.display = 'block';
    } else {
        fields.style.display = 'none';
    }
}

async function submitOrder(event) {
    event.preventDefault();
    
    // Takroriy yuborishni oldini olish
    if (isOrderSubmitting) {
        return;
    }
    
    if (!orderProductId) {
        toast("Mahsulot tanlanmagan", "error");
        return;
    }
    
    // Tugmani o'chirish
    isOrderSubmitting = true;
    var submitBtn = document.getElementById('orderSubmitBtn');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Yuklanmoqda...';
    }
    
    var body = { product_id: orderProductId };
    
    // Manzil variantini tekshirish
    var addressOption = document.querySelector('input[name="addressOption"]:checked');
    var useSaved = addressOption && addressOption.value === 'saved';
    
    if (useSaved && savedUserAddress) {
        body.use_saved_address = true;
    } else {
        // Yangi manzil ma'lumotlari
        var address = document.getElementById('orderAddress').value.trim();
        var city = document.getElementById('orderCity').value.trim();
        var country = document.getElementById('orderCountry').value.trim();
        var postalCode = document.getElementById('orderPostalCode').value.trim();
        
        if (!address || !city || !country || !postalCode) {
            toast("Barcha manzil maydonlarini to'ldiring", "error");
            // Tugmani qayta yoqish
            isOrderSubmitting = false;
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-check"></i> Buyurtma berish';
            }
            return;
        }
        
        body.address = address;
        body.city = city;
        body.country = country;
        body.postal_code = postalCode;
    }
    
    // Izoh
    var notes = document.getElementById('orderNotes').value.trim();
    if (notes) body.notes = notes;
    
    try {
        var res = await api.post("/orders/", body);
        console.log("API response status:", res.status);
        var data = await res.json();
        console.log("API response data:", data);
        
        if (res.ok || res.status === 201) {
            // Avval flaglarni tozalash
            isOrderSubmitting = false;
            orderProductId = null;
            
            // Modalni yopish - to'g'ridan-to'g'ri DOM dan o'chirish
            var modal = document.getElementById('orderModal');
            if (modal) {
                modal.remove();
                document.body.style.overflow = "";
                console.log("Modal DOM dan o'chirildi");
            }
            
            toast("Buyurtma muvaffaqiyatli yaratildi!", "success");
            showOrders();
        } else {
            toast(data.detail || "Xatolik yuz berdi", "error");
            // Tugmani qayta yoqish
            isOrderSubmitting = false;
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-check"></i> Buyurtma berish';
            }
        }
    } catch (e) {
        console.error("Order yaratishda xatolik:", e);
        toast("Xatolik yuz berdi", "error");
        // Tugmani qayta yoqish
        isOrderSubmitting = false;
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-check"></i> Buyurtma berish';
        }
    }
}

// Eski createOrder funksiyasini o'zgartirish
async function createOrder(productId) {
    showOrderModal(productId);
}

async function updateOrder(orderId, newStatus) {
    try {
        var body = { status: newStatus };
        var res = await api.patch("/orders/" + orderId + "/", body);
        var data = await res.json();
        if (res.ok) {
            toast("Buyurtma yangilandi!", "success");
            showOrders();
        } else {
            toast(data.detail || "Xatolik", "error");
        }
    } catch (e) {
        toast("Xatolik yuz berdi", "error");
    }
}

// ═══════════════ SHARH (REVIEW) ═══════════════
function showReviewForm(orderId) {
    var rating = prompt("Baho bering (1-5):");
    rating = parseInt(rating);
    if (!rating || rating < 1 || rating > 5) {
        toast("Baho 1 dan 5 gacha bo'lishi kerak", "error");
        return;
    }
    var comment = prompt("Izoh (ixtiyoriy):");
    submitReview(orderId, rating, comment || "");
}

async function submitReview(orderId, rating, comment) {
    try {
        var res = await api.post("/reviews/create/", {
            order_id: orderId,
            rating: rating,
            comment: comment
        });
        var data = await res.json();
        if (res.ok || res.status === 201) {
            toast("Sharh yuborildi!", "success");
            showOrders();
        } else {
            toast(data.detail || "Xatolik", "error");
        }
    } catch (e) {
        toast("Xatolik yuz berdi", "error");
    }
}

// ═══════════════ MENING E'LONLARIM ═══════════════
async function showMyProducts() {
    if (!isLoggedIn()) { showAuthModal(); return; }

    var content = document.getElementById("content");
    content.innerHTML = '<div class="loader"><div class="spinner"></div></div>';

    try {
        if (!currentUser) await fetchCurrentUser();

        // Faqat sotuvchilar uchun
        if (currentUser.role !== "seller") {
            content.innerHTML = '<button class="back-btn" onclick="goHome()"><i class="fas fa-arrow-left"></i> Orqaga</button>' +
                '<div class="empty-state"><i class="fas fa-store-slash"></i>' +
                '<p>Siz sotuvchi emassiz</p>' +
                '<span style="color:var(--text-secondary);font-size:.85rem;">Sotuvchi bo\'lish uchun admin bilan bog\'laning</span></div>';
            return;
        }

        var data = await api.get("/sellers/" + currentUser.id + "/products/");
        var products = data.products || data;

        var html = '<button class="back-btn" onclick="goHome()"><i class="fas fa-arrow-left"></i> Orqaga</button>' +
            '<h2 style="margin-bottom:16px"><i class="fas fa-bullhorn"></i> Mening e\'lonlarim</h2>';

        if (!products || !products.length) {
            html += '<div class="empty-state"><i class="fas fa-bullhorn"></i>' +
                '<p>Hali e\'lon joylamagan ekansiz</p>' +
                '<button class="btn btn-primary" onclick="showAddProductModal()" style="margin-top:12px">' +
                '<i class="fas fa-plus"></i> Birinchi e\'lon</button></div>';
        } else {
            html += '<div class="orders-list">';
            products.forEach(function (p) {
                var img = (p.images && p.images.length) ? p.images[0] : null;
                var imgTag = img
                    ? '<img class="order-card__img" src="' + imageUrl(img.image) + '">'
                    : '<div class="order-card__img" style="display:flex;align-items:center;justify-content:center;background:var(--bg)"><i class="fas fa-image"></i></div>';

                var actionBtns = "";
                if (p.status === "moderation") {
                    actionBtns += '<span class="badge badge-warning" style="font-size:.8rem;padding:4px 10px"><i class="fas fa-clock"></i> Admin tekshirmoqda</span>';
                }
                if (p.status === "active") {
                    actionBtns += '<button class="btn btn-outline btn-sm" onclick="archiveProduct(' + p.id + ')"><i class="fas fa-archive"></i> Arxiv</button>';
                    actionBtns += '<button class="btn btn-primary btn-sm" onclick="markSold(' + p.id + ')"><i class="fas fa-check-double"></i> Sotildi</button>';
                }
                // Tahrirlash va O'chirish — barcha holatlar uchun
                if (p.status !== "sold") {
                    actionBtns += '<button class="btn btn-warning btn-sm" onclick="showEditProductModal(' + p.id + ')" style="margin-left:4px"><i class="fas fa-edit"></i> Tahrirlash</button>';
                }
                actionBtns += '<button class="btn btn-danger btn-sm" onclick="confirmDeleteProduct(' + p.id + ', \'' + escHtml(p.title).replace(/'/g, "\\'") + '\')" style="margin-left:4px"><i class="fas fa-trash"></i> O\'chirish</button>';

                html += '<div class="order-card">' +
                    imgTag +
                    '<div class="order-card__info">' +
                        '<div class="order-card__title" style="cursor:pointer" onclick="showProductDetail(' + p.id + ')">' + escHtml(p.title) + '</div>' +
                        '<div class="order-card__meta">' +
                            statusBadge(p.status) + ' · ' +
                            formatPrice(p.price_with_tax || p.price) + " so'm · " +
                            new Date(p.created_at).toLocaleDateString("uz-UZ") +
                        '</div>' +
                    '</div>' +
                    '<div class="order-card__actions">' + actionBtns + '</div>' +
                '</div>';
            });
            html += '</div>';
        }

        content.innerHTML = html;

    } catch (e) {
        console.error("E'lonlar yuklanmadi:", e);
        content.innerHTML = '<button class="back-btn" onclick="goHome()"><i class="fas fa-arrow-left"></i> Orqaga</button>' +
            '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i>' +
            '<p>E\'lonlar yuklanmadi. Avval sotuvchi profilini yarating.</p></div>';
    }
}

async function archiveProduct(id) {
    try {
        var res = await api.post("/products/" + id + "/archive/", {});
        if (res.ok) { toast("E'lon arxivlandi!", "info"); showMyProducts(); }
        else { var d = await res.json(); toast(d.detail || "Xatolik", "error"); }
    } catch (e) { toast("Xatolik", "error"); }
}

async function markSold(id) {
    try {
        var res = await api.post("/products/" + id + "/sold/", {});
        if (res.ok) { toast("Sotildi deb belgilandi!", "success"); showMyProducts(); }
        else { var d = await res.json(); toast(d.detail || "Xatolik", "error"); }
    } catch (e) { toast("Xatolik", "error"); }
}

// ═══════════════ PROFIL ═══════════════
async function showProfile() {
    if (!isLoggedIn()) { showAuthModal(); return; }

    var content = document.getElementById("content");
    content.innerHTML = '<div class="loader"><div class="spinner"></div></div>';

    try {
        if (!currentUser) await fetchCurrentUser();

        var avatar = currentUser.username ? currentUser.username[0].toUpperCase() : "U";
        var roleName = currentUser.role === "seller" ? "Sotuvchi" : "Haridor";

        var html = '<button class="back-btn" onclick="goHome()"><i class="fas fa-arrow-left"></i> Orqaga</button>' +
            '<div class="profile-card">' +
                '<div class="profile-card__header">' +
                    '<div class="profile-card__avatar">' + avatar + '</div>' +
                    '<div>' +
                        '<div class="profile-card__name">' + escHtml(currentUser.username) + '</div>' +
                        '<div class="profile-card__role">' + roleName + ' · ' + escHtml(currentUser.email || "") + '</div>' +
                    '</div>' +
                '</div>';

        // Agar sotuvchi bo'lsa - do'kon ma'lumotlari
        if (currentUser.role === "seller") {
            try {
                var sellerRes = await api.get("/sellers/" + currentUser.id + "/");
                var s = sellerRes.seller;
                html += '<div class="profile-stats">' +
                    '<div class="profile-stat"><div class="profile-stat__num">' + (s.rating || 0).toFixed(1) + '</div><div class="profile-stat__label">Reyting</div></div>' +
                    '<div class="profile-stat"><div class="profile-stat__num">' + (s.total_sales || 0) + '</div><div class="profile-stat__label">Sotilgan</div></div>' +
                '</div>' +
                '<dl class="detail-specs">' +
                    '<dt>Do\'kon nomi</dt><dd>' + escHtml(s.shop_name) + '</dd>' +
                    (s.region ? '<dt>Viloyat</dt><dd>' + escHtml(s.region) + '</dd>' : '') +
                    (s.district ? '<dt>Tuman</dt><dd>' + escHtml(s.district) + '</dd>' : '') +
                    (s.adress ? '<dt>Manzil</dt><dd>' + escHtml(s.adress) + '</dd>' : '') +
                '</dl>';
            } catch (e) { /* seller profili yo'q */ }
        }

        // Agar haridor bo'lsa - admin bilan bog'lanish haqida xabar
        if (currentUser.role === "customer") {
            html += '<div style="margin-top:20px;padding-top:20px;border-top:1px solid var(--border)">' +
                '<div style="display:flex;align-items:center;gap:12px;padding:16px;background:var(--bg);border-radius:12px">' +
                    '<i class="fas fa-info-circle" style="font-size:1.5rem;color:var(--primary)"></i>' +
                    '<div>' +
                        '<h4 style="margin:0">Sotuvchi bo\'lmoqchimisiz?</h4>' +
                        '<p style="font-size:.85rem;color:var(--text-secondary);margin:4px 0 0">Sotuvchi bo\'lish uchun admin bilan bog\'laning. Admin sizning profilingizni sotuvchi sifatida tasdiqlaydi.</p>' +
                    '</div>' +
                '</div>' +
            '</div>';
        }

        html += '<button class="btn btn-danger" style="margin-top:24px" onclick="handleLogout()">' +
            '<i class="fas fa-sign-out-alt"></i> Chiqish</button>' +
        '</div>';

        content.innerHTML = html;

    } catch (e) {
        console.error("Profil yuklanmadi:", e);
    }
}

// ═══════════════ E'LON QO'SHISH ═══════════════
async function showAddProductModal() {
    if (!isLoggedIn()) { showAuthModal(); return; }
    if (!currentUser) await fetchCurrentUser();

    // Faqat sotuvchilar mahsulot qo'sha oladi
    if (currentUser.role !== "seller") {
        toast("Faqat sotuvchilar mahsulot qo'sha oladi. Admin bilan bog'laning.", "error");
        return;
    }

    // Reset form avval
    document.getElementById("addProductForm").reset();
    document.getElementById("imagePreview").innerHTML = "";
    hideAllAttrFields();
    document.getElementById("pricePreview").style.display = "none";

    // Kategoriyalar — har safar yangilab olish (kesh muammosini oldini olish)
    if (!categoriesCache || categoriesCache.length === 0) {
        try {
            categoriesCache = await api.get("/categories/");
            renderCategoryList();
        } catch (e) {
            console.error("Kategoriyalar yuklanmadi:", e);
        }
    }

    var catSelect = document.getElementById("prodCategory");
    catSelect.innerHTML = '<option value="">Tanlang...</option>';
    categoriesCache.forEach(function (cat) {
        catSelect.innerHTML += '<option value="' + cat.id + '" data-type="' + cat.category_type + '">' + escHtml(cat.name) + '</option>';
    });

    openModal("addProductModal");
}

function onCategoryChange() {
    var select = document.getElementById("prodCategory");
    var selected = select.options[select.selectedIndex];
    var type = selected ? selected.getAttribute("data-type") : "";

    hideAllAttrFields();

    var fieldMap = {
        phone: "phoneFields",
        tv: "tvFields",
        laptop: "laptopFields",
        clothing: "clothingFields",
        shoes: "shoesFields",
        appliance: "applianceFields",
        auto: "autoFields",
        food: "foodFields",
        furniture: "furnitureFields",
        book: "bookFields",
        hobby: "hobbyFields",
        other: "otherFields"
    };

    if (type && fieldMap[type]) {
        document.getElementById(fieldMap[type]).style.display = "block";
    }
}

function hideAllAttrFields() {
    var ids = [
        "phoneFields", "tvFields", "laptopFields", "clothingFields",
        "shoesFields", "applianceFields", "autoFields", "foodFields",
        "furnitureFields", "bookFields", "hobbyFields", "otherFields"
    ];
    ids.forEach(function (id) {
        var el = document.getElementById(id);
        if (el) el.style.display = "none";
    });
}

// ── Narx + soliq preview ──
function setupPricePreview() {
    var priceInput = document.getElementById("prodPrice");
    var taxInput = document.getElementById("prodTax");
    if (priceInput) priceInput.addEventListener("input", updatePricePreview);
    if (taxInput) taxInput.addEventListener("input", updatePricePreview);
}

function updatePricePreview() {
    var price = parseFloat(document.getElementById("prodPrice").value) || 0;
    var taxPct = parseFloat(document.getElementById("prodTax").value) || 0;
    var preview = document.getElementById("pricePreview");

    if (price > 0) {
        var taxAmount = price * taxPct / 100;
        var total = price + taxAmount;
        document.getElementById("prevPrice").textContent = formatPrice(price) + " so'm";
        document.getElementById("prevTaxPct").textContent = taxPct;
        document.getElementById("prevTax").textContent = "+" + formatPrice(taxAmount) + " so'm";
        document.getElementById("prevTotal").textContent = formatPrice(total) + " so'm";
        preview.style.display = "block";
    } else {
        preview.style.display = "none";
    }
}

function previewImages(input) {
    var preview = document.getElementById("imagePreview");
    preview.innerHTML = "";
    var files = input.files;
    for (var i = 0; i < Math.min(files.length, 10); i++) {
        var reader = new FileReader();
        reader.onload = function (e) {
            preview.innerHTML += '<img src="' + e.target.result + '">';
        };
        reader.readAsDataURL(files[i]);
    }
}

async function handleAddProduct(e) {
    e.preventDefault();

    var catSelect = document.getElementById("prodCategory");
    var selectedOpt = catSelect.options[catSelect.selectedIndex];
    var catType = selectedOpt ? selectedOpt.getAttribute("data-type") : "";

    var body = {
        category: parseInt(catSelect.value),
        title: document.getElementById("prodTitle").value.trim(),
        description: document.getElementById("prodDescription").value.trim(),
        price: document.getElementById("prodPrice").value,
        tax_percent: document.getElementById("prodTax").value || "0",
    };

    var brandVal = document.getElementById("prodBrand").value;
    if (brandVal) body.brand_id = parseInt(brandVal);

    // Atributlar — 12 ta kategoriya turi
    if (catType === "phone") {
        var attr = {};
        var v;
        v = document.getElementById("attrPhoneModel").value; if (v) attr.model_name = v;
        v = document.getElementById("attrPhoneStorage").value; if (v) attr.storage_gb = parseInt(v);
        v = document.getElementById("attrPhoneRam").value; if (v) attr.ram_gb = parseInt(v);
        v = document.getElementById("attrPhoneBattery").value; if (v) attr.battery_mah = parseInt(v);
        v = document.getElementById("attrPhoneScreen").value; if (v) attr.screen_size = v;
        v = document.getElementById("attrPhoneCamera").value; if (v) attr.camera_mp = parseInt(v);
        v = document.getElementById("attrPhoneOS").value; if (v) attr.os = v;
        v = document.getElementById("attrPhoneSim").value; if (v) attr.sim_count = parseInt(v);
        body.phone_attr = attr;
    }

    if (catType === "tv") {
        var attr = {};
        var v;
        v = document.getElementById("attrTvModel").value; if (v) attr.model_name = v;
        v = document.getElementById("attrTvScreen").value; if (v) attr.screen_size = parseInt(v);
        v = document.getElementById("attrTvResolution").value; if (v) attr.resolution = v;
        v = document.getElementById("attrTvRefresh").value; if (v) attr.refresh_rate = parseInt(v);
        attr.is_smart = document.getElementById("attrTvSmart").checked;
        v = document.getElementById("attrTvWarranty").value; if (v) attr.warranty_months = parseInt(v);
        body.tv_attr = attr;
    }

    if (catType === "laptop") {
        var attr = {};
        var v;
        v = document.getElementById("attrLaptopModel").value; if (v) attr.model_name = v;
        v = document.getElementById("attrLaptopProcessor").value; if (v) attr.processor = v;
        v = document.getElementById("attrLaptopRam").value; if (v) attr.ram_gb = parseInt(v);
        v = document.getElementById("attrLaptopStorage").value; if (v) attr.storage_gb = parseInt(v);
        v = document.getElementById("attrLaptopStorageType").value; if (v) attr.storage_type = v;
        v = document.getElementById("attrLaptopScreen").value; if (v) attr.screen_size = v;
        v = document.getElementById("attrLaptopBattery").value; if (v) attr.battery_hours = parseInt(v);
        v = document.getElementById("attrLaptopOS").value; if (v) attr.os = v;
        v = document.getElementById("attrLaptopWarranty").value; if (v) attr.warranty_months = parseInt(v);
        body.laptop_attr = attr;
    }

    if (catType === "clothing") {
        var attr = {};
        var v;
        // Tanlangan razmerlarni yig'ish
        var selectedSizes = [];
        document.querySelectorAll("#clothingSizeCheckboxes input[type=checkbox]:checked").forEach(function (cb) {
            selectedSizes.push(cb.value);
        });
        if (selectedSizes.length) attr.available_sizes = selectedSizes;
        v = document.getElementById("attrClothingGender").value; if (v) attr.gender = v;
        v = document.getElementById("attrClothingSeason").value; if (v) attr.season = v;
        v = document.getElementById("attrClothingMaterial").value; if (v) attr.material = v;
        body.clothing_attr = attr;
    }

    if (catType === "shoes") {
        var attr = {};
        var v;
        // Tanlangan razmerlarni yig'ish
        var selectedSizes = [];
        document.querySelectorAll("#shoesSizeCheckboxes input[type=checkbox]:checked").forEach(function (cb) {
            selectedSizes.push(parseInt(cb.value));
        });
        if (selectedSizes.length) attr.available_sizes = selectedSizes;
        v = document.getElementById("attrShoesGender").value; if (v) attr.gender = v;
        v = document.getElementById("attrShoesSeason").value; if (v) attr.season = v;
        v = document.getElementById("attrShoesMaterial").value; if (v) attr.material = v;
        body.shoes_attr = attr;
    }

    if (catType === "appliance") {
        var attr = {};
        var v;
        v = document.getElementById("attrApplianceModel").value; if (v) attr.model_name = v;
        v = document.getElementById("attrAppliancePower").value; if (v) attr.power_watt = parseInt(v);
        v = document.getElementById("attrApplianceEnergy").value; if (v) attr.energy_class = v;
        v = document.getElementById("attrApplianceWeight").value; if (v) attr.weight_kg = v;
        v = document.getElementById("attrApplianceDimensions").value; if (v) attr.dimensions = v;
        v = document.getElementById("attrApplianceWarranty").value; if (v) attr.warranty_months = parseInt(v);
        body.appliance_attr = attr;
    }

    if (catType === "auto") {
        var attr = {};
        var v;
        v = document.getElementById("attrAutoMake").value; if (v) attr.make = v;
        v = document.getElementById("attrAutoModel").value; if (v) attr.model_name = v;
        v = document.getElementById("attrAutoYear").value; if (v) attr.year = parseInt(v);
        v = document.getElementById("attrAutoFuel").value; if (v) attr.fuel_type = v;
        v = document.getElementById("attrAutoTransmission").value; if (v) attr.transmission = v;
        v = document.getElementById("attrAutoDrive").value; if (v) attr.drive_type = v;
        v = document.getElementById("attrAutoMileage").value; if (v) attr.mileage_km = parseInt(v);
        v = document.getElementById("attrAutoEngine").value; if (v) attr.engine_cc = parseInt(v);
        body.auto_attr = attr;
    }

    if (catType === "food") {
        var attr = {};
        var v;
        v = document.getElementById("attrFoodExpiry").value; if (v) attr.expiry_date = v;
        v = document.getElementById("attrFoodWeight").value; if (v) attr.weight = v;
        v = document.getElementById("attrFoodWeightUnit").value; if (v) attr.weight_unit = v;
        attr.is_organic = document.getElementById("attrFoodOrganic").checked;
        v = document.getElementById("attrFoodIngredients").value; if (v) attr.ingredients = v;
        v = document.getElementById("attrFoodStorage").value; if (v) attr.storage_info = v;
        body.food_attr = attr;
    }

    if (catType === "furniture") {
        var attr = {};
        var v;
        v = document.getElementById("attrFurnitureMaterial").value; if (v) attr.material = v;
        v = document.getElementById("attrFurnitureDimensions").value; if (v) attr.dimensions = v;
        v = document.getElementById("attrFurnitureWeight").value; if (v) attr.weight_kg = v;
        v = document.getElementById("attrFurnitureWarranty").value; if (v) attr.warranty_months = parseInt(v);
        body.furniture_attr = attr;
    }

    if (catType === "book") {
        var attr = {};
        var v;
        v = document.getElementById("attrBookAuthor").value; if (v) attr.author = v;
        v = document.getElementById("attrBookPublisher").value; if (v) attr.publisher = v;
        v = document.getElementById("attrBookLanguage").value; if (v) attr.language = v;
        v = document.getElementById("attrBookPages").value; if (v) attr.pages = parseInt(v);
        v = document.getElementById("attrBookIsbn").value; if (v) attr.isbn = v;
        v = document.getElementById("attrBookGenre").value; if (v) attr.genre = v;
        body.book_attr = attr;
    }

    if (catType === "hobby") {
        var attr = {};
        var v;
        v = document.getElementById("attrHobbyType").value; if (v) attr.hobby_type = v;
        v = document.getElementById("attrHobbyMaterial").value; if (v) attr.material = v;
        v = document.getElementById("attrHobbyAgeMin").value; if (v) attr.age_min = parseInt(v);
        v = document.getElementById("attrHobbyAgeMax").value; if (v) attr.age_max = parseInt(v);
        body.hobby_attr = attr;
    }

    if (catType === "other") {
        var attr = {};
        var v;
        v = document.getElementById("attrOtherMaterial").value; if (v) attr.material = v;
        v = document.getElementById("attrOtherWeight").value; if (v) attr.weight_kg = v;
        v = document.getElementById("attrOtherWarranty").value; if (v) attr.warranty_months = parseInt(v);
        body.other_attr = attr;
    }

    try {
        console.log("📤 E'lon joylash — body:", JSON.stringify(body));
        var res = await api.post("/products/", body);
        console.log("📥 Server javob:", res.status, res.statusText);
        var data = await res.json();
        console.log("📥 Server data:", data);

        if (res.ok || res.status === 201) {
            toast("E'lon muvaffaqiyatli joylandi!", "success");

            // Rasmlar yuklash
            var fileInput = document.getElementById("prodImages");
            if (fileInput.files.length > 0) {
                var formData = new FormData();
                for (var i = 0; i < Math.min(fileInput.files.length, 10); i++) {
                    formData.append("images", fileInput.files[i]);
                }
                await api.upload("/products/" + data.id + "/images/", formData);
            }

            closeModal("addProductModal");
            showMyProducts();
        } else {
            var errMsg = "";
            if (typeof data === "object") {
                Object.keys(data).forEach(function (key) {
                    errMsg += key + ": " + data[key] + "\n";
                });
            }
            toast(errMsg || "Xatolik yuz berdi", "error");
        }
    } catch (e) {
        console.error("E'lon joylashda xatolik:", e);
        toast("Server bilan bog'lanib bo'lmadi", "error");
    }
}

// ═══════════════ TAHRIRLASH & O'CHIRISH ═══════════════

async function showEditProductModal(id) {
    try {
        var p = await api.get("/products/" + id + "/");

        // Kategoriyalar keshini yangilash
        if (!categoriesCache || categoriesCache.length === 0) {
            try {
                categoriesCache = await api.get("/categories/");
                renderCategoryList();
            } catch (e) {
                console.error("Kategoriyalar yuklanmadi:", e);
            }
        }

        document.getElementById("editProdId").value = p.id;
        document.getElementById("editProdTitle").value = p.title || "";
        document.getElementById("editProdDescription").value = p.description || "";
        document.getElementById("editProdPrice").value = p.price || "";
        document.getElementById("editProdTax").value = p.tax_percent || "";

        // Kategoriyalar — faqat ko'rsatish, o'zgartirish mumkin emas
        var catSelect = document.getElementById("editProdCategory");
        catSelect.innerHTML = '<option value="">Tanlang...</option>';
        categoriesCache.forEach(function (cat) {
            var sel = (p.category === cat.id) ? " selected" : "";
            catSelect.innerHTML += '<option value="' + cat.id + '" data-type="' + cat.category_type + '"' + sel + '>' + escHtml(cat.name) + '</option>';
        });
        catSelect.disabled = true;
        catSelect.style.opacity = "0.6";
        catSelect.style.cursor = "not-allowed";

        // Brendlar
        var brandSelect = document.getElementById("editProdBrand");
        brandSelect.innerHTML = '<option value="">Tanlanmagan</option>';
        if (brandsCache && brandsCache.length) {
            brandsCache.forEach(function (b) {
                var sel = (p.brand && p.brand.id === b.id) ? " selected" : "";
                brandSelect.innerHTML += '<option value="' + b.id + '"' + sel + '>' + escHtml(b.name) + '</option>';
            });
        }

        // Atribut maydonlarini ko'rsatish
        hideAllEditAttrFields();
        var selectedOpt = catSelect.options[catSelect.selectedIndex];
        var catType = selectedOpt ? selectedOpt.getAttribute("data-type") : "";
        document.getElementById("editProdCatType").value = catType || "";

        if (catType) {
            fillEditAttrFields(p, catType);
        }

        openModal("editProductModal");
    } catch (e) {
        console.error("Mahsulot yuklanmadi:", e);
        toast("Mahsulot ma'lumotlarini olishda xatolik", "error");
    }
}

function onEditCategoryChange() {
    var select = document.getElementById("editProdCategory");
    var selected = select.options[select.selectedIndex];
    var type = selected ? selected.getAttribute("data-type") : "";

    document.getElementById("editProdCatType").value = type || "";
    hideAllEditAttrFields();

    var fieldMap = {
        phone: "editPhoneFields",
        tv: "editTvFields",
        laptop: "editLaptopFields",
        clothing: "editClothingFields",
        shoes: "editShoesFields",
        appliance: "editApplianceFields",
        auto: "editAutoFields",
        food: "editFoodFields",
        furniture: "editFurnitureFields",
        book: "editBookFields",
        hobby: "editHobbyFields",
        other: "editOtherFields"
    };

    if (type && fieldMap[type]) {
        document.getElementById(fieldMap[type]).style.display = "block";
    }
}

function hideAllEditAttrFields() {
    var ids = [
        "editPhoneFields", "editTvFields", "editLaptopFields", "editClothingFields",
        "editShoesFields", "editApplianceFields", "editAutoFields", "editFoodFields",
        "editFurnitureFields", "editBookFields", "editHobbyFields", "editOtherFields"
    ];
    ids.forEach(function (id) {
        var el = document.getElementById(id);
        if (el) el.style.display = "none";
    });
}

function fillEditAttrFields(product, catType) {
    var fieldMap = {
        phone: "editPhoneFields",
        tv: "editTvFields",
        laptop: "editLaptopFields",
        clothing: "editClothingFields",
        shoes: "editShoesFields",
        appliance: "editApplianceFields",
        auto: "editAutoFields",
        food: "editFoodFields",
        furniture: "editFurnitureFields",
        book: "editBookFields",
        hobby: "editHobbyFields",
        other: "editOtherFields"
    };

    if (!fieldMap[catType]) return;
    document.getElementById(fieldMap[catType]).style.display = "block";

    if (catType === "phone" && product.phone_attr) {
        var a = product.phone_attr;
        document.getElementById("editAttrPhoneModel").value = a.model_name || "";
        document.getElementById("editAttrPhoneStorage").value = a.storage_gb || "";
        document.getElementById("editAttrPhoneRam").value = a.ram_gb || "";
        document.getElementById("editAttrPhoneBattery").value = a.battery_mah || "";
        document.getElementById("editAttrPhoneScreen").value = a.screen_size || "";
        document.getElementById("editAttrPhoneCamera").value = a.camera_mp || "";
        document.getElementById("editAttrPhoneOS").value = a.os || "";
        document.getElementById("editAttrPhoneSim").value = a.sim_count || "";
    }

    if (catType === "tv" && product.tv_attr) {
        var a = product.tv_attr;
        document.getElementById("editAttrTvModel").value = a.model_name || "";
        document.getElementById("editAttrTvScreen").value = a.screen_size || "";
        document.getElementById("editAttrTvResolution").value = a.resolution || "";
        document.getElementById("editAttrTvRefresh").value = a.refresh_rate || "";
        document.getElementById("editAttrTvSmart").checked = !!a.is_smart;
        document.getElementById("editAttrTvWarranty").value = a.warranty_months || "";
    }

    if (catType === "laptop" && product.laptop_attr) {
        var a = product.laptop_attr;
        document.getElementById("editAttrLaptopModel").value = a.model_name || "";
        document.getElementById("editAttrLaptopProcessor").value = a.processor || "";
        document.getElementById("editAttrLaptopRam").value = a.ram_gb || "";
        document.getElementById("editAttrLaptopStorage").value = a.storage_gb || "";
        document.getElementById("editAttrLaptopStorageType").value = a.storage_type || "";
        document.getElementById("editAttrLaptopScreen").value = a.screen_size || "";
        document.getElementById("editAttrLaptopBattery").value = a.battery_hours || "";
        document.getElementById("editAttrLaptopOS").value = a.os || "";
        document.getElementById("editAttrLaptopWarranty").value = a.warranty_months || "";
    }

    if (catType === "clothing" && product.clothing_attr) {
        var a = product.clothing_attr;
        document.querySelectorAll("#editClothingSizeCheckboxes input[type=checkbox]").forEach(function (cb) {
            cb.checked = (a.available_sizes && a.available_sizes.indexOf(cb.value) !== -1);
        });
        document.getElementById("editAttrClothingGender").value = a.gender || "";
        document.getElementById("editAttrClothingSeason").value = a.season || "";
        document.getElementById("editAttrClothingMaterial").value = a.material || "";
    }

    if (catType === "shoes" && product.shoes_attr) {
        var a = product.shoes_attr;
        document.querySelectorAll("#editShoesSizeCheckboxes input[type=checkbox]").forEach(function (cb) {
            cb.checked = (a.available_sizes && a.available_sizes.indexOf(parseInt(cb.value)) !== -1);
        });
        document.getElementById("editAttrShoesGender").value = a.gender || "";
        document.getElementById("editAttrShoesSeason").value = a.season || "";
        document.getElementById("editAttrShoesMaterial").value = a.material || "";
    }

    if (catType === "appliance" && product.appliance_attr) {
        var a = product.appliance_attr;
        document.getElementById("editAttrApplianceModel").value = a.model_name || "";
        document.getElementById("editAttrAppliancePower").value = a.power_watt || "";
        document.getElementById("editAttrApplianceEnergy").value = a.energy_class || "";
        document.getElementById("editAttrApplianceWeight").value = a.weight_kg || "";
        document.getElementById("editAttrApplianceDimensions").value = a.dimensions || "";
        document.getElementById("editAttrApplianceWarranty").value = a.warranty_months || "";
    }

    if (catType === "auto" && product.auto_attr) {
        var a = product.auto_attr;
        document.getElementById("editAttrAutoMake").value = a.make || "";
        document.getElementById("editAttrAutoModel").value = a.model_name || "";
        document.getElementById("editAttrAutoYear").value = a.year || "";
        document.getElementById("editAttrAutoFuel").value = a.fuel_type || "";
        document.getElementById("editAttrAutoTransmission").value = a.transmission || "";
        document.getElementById("editAttrAutoDrive").value = a.drive_type || "";
        document.getElementById("editAttrAutoMileage").value = a.mileage_km || "";
        document.getElementById("editAttrAutoEngine").value = a.engine_cc || "";
    }

    if (catType === "food" && product.food_attr) {
        var a = product.food_attr;
        document.getElementById("editAttrFoodExpiry").value = a.expiry_date || "";
        document.getElementById("editAttrFoodWeight").value = a.weight || "";
        document.getElementById("editAttrFoodWeightUnit").value = a.weight_unit || "kg";
        document.getElementById("editAttrFoodOrganic").checked = !!a.is_organic;
        document.getElementById("editAttrFoodIngredients").value = a.ingredients || "";
        document.getElementById("editAttrFoodStorage").value = a.storage_info || "";
    }

    if (catType === "furniture" && product.furniture_attr) {
        var a = product.furniture_attr;
        document.getElementById("editAttrFurnitureMaterial").value = a.material || "";
        document.getElementById("editAttrFurnitureDimensions").value = a.dimensions || "";
        document.getElementById("editAttrFurnitureWeight").value = a.weight_kg || "";
        document.getElementById("editAttrFurnitureWarranty").value = a.warranty_months || "";
    }

    if (catType === "book" && product.book_attr) {
        var a = product.book_attr;
        document.getElementById("editAttrBookAuthor").value = a.author || "";
        document.getElementById("editAttrBookPublisher").value = a.publisher || "";
        document.getElementById("editAttrBookLanguage").value = a.language || "";
        document.getElementById("editAttrBookPages").value = a.pages || "";
        document.getElementById("editAttrBookIsbn").value = a.isbn || "";
        document.getElementById("editAttrBookGenre").value = a.genre || "";
    }

    if (catType === "hobby" && product.hobby_attr) {
        var a = product.hobby_attr;
        document.getElementById("editAttrHobbyType").value = a.hobby_type || "";
        document.getElementById("editAttrHobbyMaterial").value = a.material || "";
        document.getElementById("editAttrHobbyAgeMin").value = a.age_min || "";
        document.getElementById("editAttrHobbyAgeMax").value = a.age_max || "";
    }

    if (catType === "other" && product.other_attr) {
        var a = product.other_attr;
        document.getElementById("editAttrOtherMaterial").value = a.material || "";
        document.getElementById("editAttrOtherWeight").value = a.weight_kg || "";
        document.getElementById("editAttrOtherWarranty").value = a.warranty_months || "";
    }
}

async function handleEditProduct(e) {
    e.preventDefault();

    var prodId = document.getElementById("editProdId").value;
    var catSelect = document.getElementById("editProdCategory");
    var selectedOpt = catSelect.options[catSelect.selectedIndex];
    var catType = selectedOpt ? selectedOpt.getAttribute("data-type") : "";

    var body = {
        title: document.getElementById("editProdTitle").value.trim(),
        description: document.getElementById("editProdDescription").value.trim(),
        price: document.getElementById("editProdPrice").value,
        tax_percent: document.getElementById("editProdTax").value || "0",
    };

    var brandVal = document.getElementById("editProdBrand").value;
    if (brandVal) body.brand_id = parseInt(brandVal);

    // Atributlar — 12 ta kategoriya turi
    if (catType === "phone") {
        var attr = {}; var v;
        v = document.getElementById("editAttrPhoneModel").value; if (v) attr.model_name = v;
        v = document.getElementById("editAttrPhoneStorage").value; if (v) attr.storage_gb = parseInt(v);
        v = document.getElementById("editAttrPhoneRam").value; if (v) attr.ram_gb = parseInt(v);
        v = document.getElementById("editAttrPhoneBattery").value; if (v) attr.battery_mah = parseInt(v);
        v = document.getElementById("editAttrPhoneScreen").value; if (v) attr.screen_size = v;
        v = document.getElementById("editAttrPhoneCamera").value; if (v) attr.camera_mp = parseInt(v);
        v = document.getElementById("editAttrPhoneOS").value; if (v) attr.os = v;
        v = document.getElementById("editAttrPhoneSim").value; if (v) attr.sim_count = parseInt(v);
        body.phone_attr = attr;
    }

    if (catType === "tv") {
        var attr = {}; var v;
        v = document.getElementById("editAttrTvModel").value; if (v) attr.model_name = v;
        v = document.getElementById("editAttrTvScreen").value; if (v) attr.screen_size = parseInt(v);
        v = document.getElementById("editAttrTvResolution").value; if (v) attr.resolution = v;
        v = document.getElementById("editAttrTvRefresh").value; if (v) attr.refresh_rate = parseInt(v);
        attr.is_smart = document.getElementById("editAttrTvSmart").checked;
        v = document.getElementById("editAttrTvWarranty").value; if (v) attr.warranty_months = parseInt(v);
        body.tv_attr = attr;
    }

    if (catType === "laptop") {
        var attr = {}; var v;
        v = document.getElementById("editAttrLaptopModel").value; if (v) attr.model_name = v;
        v = document.getElementById("editAttrLaptopProcessor").value; if (v) attr.processor = v;
        v = document.getElementById("editAttrLaptopRam").value; if (v) attr.ram_gb = parseInt(v);
        v = document.getElementById("editAttrLaptopStorage").value; if (v) attr.storage_gb = parseInt(v);
        v = document.getElementById("editAttrLaptopStorageType").value; if (v) attr.storage_type = v;
        v = document.getElementById("editAttrLaptopScreen").value; if (v) attr.screen_size = v;
        v = document.getElementById("editAttrLaptopBattery").value; if (v) attr.battery_hours = parseInt(v);
        v = document.getElementById("editAttrLaptopOS").value; if (v) attr.os = v;
        v = document.getElementById("editAttrLaptopWarranty").value; if (v) attr.warranty_months = parseInt(v);
        body.laptop_attr = attr;
    }

    if (catType === "clothing") {
        var attr = {}; var v;
        var selectedSizes = [];
        document.querySelectorAll("#editClothingSizeCheckboxes input[type=checkbox]:checked").forEach(function (cb) {
            selectedSizes.push(cb.value);
        });
        if (selectedSizes.length) attr.available_sizes = selectedSizes;
        v = document.getElementById("editAttrClothingGender").value; if (v) attr.gender = v;
        v = document.getElementById("editAttrClothingSeason").value; if (v) attr.season = v;
        v = document.getElementById("editAttrClothingMaterial").value; if (v) attr.material = v;
        body.clothing_attr = attr;
    }

    if (catType === "shoes") {
        var attr = {}; var v;
        var selectedSizes = [];
        document.querySelectorAll("#editShoesSizeCheckboxes input[type=checkbox]:checked").forEach(function (cb) {
            selectedSizes.push(parseInt(cb.value));
        });
        if (selectedSizes.length) attr.available_sizes = selectedSizes;
        v = document.getElementById("editAttrShoesGender").value; if (v) attr.gender = v;
        v = document.getElementById("editAttrShoesSeason").value; if (v) attr.season = v;
        v = document.getElementById("editAttrShoesMaterial").value; if (v) attr.material = v;
        body.shoes_attr = attr;
    }

    if (catType === "appliance") {
        var attr = {}; var v;
        v = document.getElementById("editAttrApplianceModel").value; if (v) attr.model_name = v;
        v = document.getElementById("editAttrAppliancePower").value; if (v) attr.power_watt = parseInt(v);
        v = document.getElementById("editAttrApplianceEnergy").value; if (v) attr.energy_class = v;
        v = document.getElementById("editAttrApplianceWeight").value; if (v) attr.weight_kg = v;
        v = document.getElementById("editAttrApplianceDimensions").value; if (v) attr.dimensions = v;
        v = document.getElementById("editAttrApplianceWarranty").value; if (v) attr.warranty_months = parseInt(v);
        body.appliance_attr = attr;
    }

    if (catType === "auto") {
        var attr = {}; var v;
        v = document.getElementById("editAttrAutoMake").value; if (v) attr.make = v;
        v = document.getElementById("editAttrAutoModel").value; if (v) attr.model_name = v;
        v = document.getElementById("editAttrAutoYear").value; if (v) attr.year = parseInt(v);
        v = document.getElementById("editAttrAutoFuel").value; if (v) attr.fuel_type = v;
        v = document.getElementById("editAttrAutoTransmission").value; if (v) attr.transmission = v;
        v = document.getElementById("editAttrAutoDrive").value; if (v) attr.drive_type = v;
        v = document.getElementById("editAttrAutoMileage").value; if (v) attr.mileage_km = parseInt(v);
        v = document.getElementById("editAttrAutoEngine").value; if (v) attr.engine_cc = parseInt(v);
        body.auto_attr = attr;
    }

    if (catType === "food") {
        var attr = {}; var v;
        v = document.getElementById("editAttrFoodExpiry").value; if (v) attr.expiry_date = v;
        v = document.getElementById("editAttrFoodWeight").value; if (v) attr.weight = v;
        v = document.getElementById("editAttrFoodWeightUnit").value; if (v) attr.weight_unit = v;
        attr.is_organic = document.getElementById("editAttrFoodOrganic").checked;
        v = document.getElementById("editAttrFoodIngredients").value; if (v) attr.ingredients = v;
        v = document.getElementById("editAttrFoodStorage").value; if (v) attr.storage_info = v;
        body.food_attr = attr;
    }

    if (catType === "furniture") {
        var attr = {}; var v;
        v = document.getElementById("editAttrFurnitureMaterial").value; if (v) attr.material = v;
        v = document.getElementById("editAttrFurnitureDimensions").value; if (v) attr.dimensions = v;
        v = document.getElementById("editAttrFurnitureWeight").value; if (v) attr.weight_kg = v;
        v = document.getElementById("editAttrFurnitureWarranty").value; if (v) attr.warranty_months = parseInt(v);
        body.furniture_attr = attr;
    }

    if (catType === "book") {
        var attr = {}; var v;
        v = document.getElementById("editAttrBookAuthor").value; if (v) attr.author = v;
        v = document.getElementById("editAttrBookPublisher").value; if (v) attr.publisher = v;
        v = document.getElementById("editAttrBookLanguage").value; if (v) attr.language = v;
        v = document.getElementById("editAttrBookPages").value; if (v) attr.pages = parseInt(v);
        v = document.getElementById("editAttrBookIsbn").value; if (v) attr.isbn = v;
        v = document.getElementById("editAttrBookGenre").value; if (v) attr.genre = v;
        body.book_attr = attr;
    }

    if (catType === "hobby") {
        var attr = {}; var v;
        v = document.getElementById("editAttrHobbyType").value; if (v) attr.hobby_type = v;
        v = document.getElementById("editAttrHobbyMaterial").value; if (v) attr.material = v;
        v = document.getElementById("editAttrHobbyAgeMin").value; if (v) attr.age_min = parseInt(v);
        v = document.getElementById("editAttrHobbyAgeMax").value; if (v) attr.age_max = parseInt(v);
        body.hobby_attr = attr;
    }

    if (catType === "other") {
        var attr = {}; var v;
        v = document.getElementById("editAttrOtherMaterial").value; if (v) attr.material = v;
        v = document.getElementById("editAttrOtherWeight").value; if (v) attr.weight_kg = v;
        v = document.getElementById("editAttrOtherWarranty").value; if (v) attr.warranty_months = parseInt(v);
        body.other_attr = attr;
    }

    try {
        console.log("Tahrirlash body:", JSON.stringify(body));
        var res = await api.patch("/products/" + prodId + "/", body);
        var data = await res.json();
        console.log("Server javob:", res.status, data);

        if (res.ok) {
            toast("O'zgarishlar moderatsiyaga yuborildi. Admin tasdiqlashini kuting.", "info");
            closeModal("editProductModal");
            showMyProducts();
        } else {
            var errMsg = "";
            if (typeof data === "object") {
                Object.keys(data).forEach(function (key) {
                    errMsg += key + ": " + data[key] + "\n";
                });
            }
            toast(errMsg || "Xatolik yuz berdi", "error");
        }
    } catch (e) {
        console.error("Tahrirlashda xatolik:", e);
        toast("Server bilan bog'lanib bo'lmadi", "error");
    }
}

// ── O'chirish ──
var pendingDeleteId = null;

function confirmDeleteProduct(id, title) {
    pendingDeleteId = id;
    document.getElementById("confirmTitle").textContent = "E'lonni o'chirish";
    document.getElementById("confirmText").textContent = '"' + title + '" \u2014 bu e\'lonni o\'chirishni xohlaysizmi? Bu amalni qaytarib bo\'lmaydi.';
    document.getElementById("confirmBtn").setAttribute("onclick", "deleteProduct()");
    openModal("confirmModal");
}

async function deleteProduct() {
    if (!pendingDeleteId) return;
    closeModal("confirmModal");

    try {
        var res = await api.delete("/products/" + pendingDeleteId + "/");
        if (res.ok || res.status === 204) {
            toast("E'lon o'chirildi!", "info");
            pendingDeleteId = null;
            showMyProducts();
        } else {
            var data = {};
            try { data = await res.json(); } catch (ex) { /* empty */ }
            toast(data.detail || "O'chirishda xatolik", "error");
        }
    } catch (e) {
        console.error("O'chirishda xatolik:", e);
        toast("Server bilan bog'lanib bo'lmadi", "error");
    }
}
