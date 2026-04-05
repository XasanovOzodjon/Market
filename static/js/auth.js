/* ═══════════════════════════════════════════
   AUTH — Login / Register / Logout
   ═══════════════════════════════════════════ */

let currentUser = null;
let regUid = null; // email tasdiqlash uchun

function isLoggedIn() {
    return !!getAccessToken();
}

// ── UI yangilash ──
function updateAuthUI() {
    const logged = isLoggedIn();
    const isSeller = logged && currentUser && currentUser.role === "seller";

    var loginBtn = document.getElementById("loginBtn");
    var profileBtn = document.getElementById("profileBtn");
    var favoritesBtn = document.getElementById("favoritesBtn");
    var ordersBtn = document.getElementById("ordersBtn");
    var myProductsBtn = document.getElementById("myProductsBtn");
    var fabAdd = document.getElementById("fabAdd");

    if (loginBtn) loginBtn.style.display = logged ? "none" : "flex";
    if (profileBtn) profileBtn.style.display = logged ? "flex" : "none";
    if (favoritesBtn) favoritesBtn.style.display = logged ? "flex" : "none";
    if (ordersBtn) ordersBtn.style.display = logged ? "flex" : "none";

    // Faqat sotuvchilar uchun
    if (myProductsBtn) myProductsBtn.style.display = isSeller ? "flex" : "none";
    if (fabAdd) fabAdd.style.display = isSeller ? "flex" : "none";

    if (logged && currentUser) {
        var profileName = document.getElementById("profileName");
        if (profileName) profileName.textContent = currentUser.username || "Profil";
    }
}

// ── Google OAuth callback tekshirish ──
function checkGoogleCallback() {
    var params = new URLSearchParams(window.location.search);
    if (params.get("google_auth") === "success") {
        var access = params.get("access");
        var refresh = params.get("refresh");
        if (access && refresh) {
            setTokens(access, refresh);
            // URL dan parametrlarni tozalash
            window.history.replaceState({}, document.title, "/");
            toast("Google orqali muvaffaqiyatli kirdingiz!", "success");
        }
    } else if (params.get("error")) {
        toast("Google auth xatolik: " + params.get("error"), "error");
        window.history.replaceState({}, document.title, "/");
    }
}

// ── Foydalanuvchi ma'lumotlarini olish ──
async function fetchCurrentUser() {
    if (!isLoggedIn()) return;
    try {
        currentUser = await api.get("/users/me");
    } catch (e) {
        console.error("User fetch xatolik:", e);
    }
    updateAuthUI();
}

// ── Modal ko'rsatish ──
function showAuthModal() {
    openModal("authModal");
}

function switchAuthTab(tab) {
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    const pinSection = document.getElementById("pinSection");
    
    // Null tekshiruvi
    if (!loginForm || !registerForm) {
        console.error('Forms not found');
        return;
    }
    
    document.getElementById("tabLogin").classList.toggle("active", tab === "login");
    document.getElementById("tabRegister").classList.toggle("active", tab === "register");
    loginForm.style.display = tab === "login" ? "flex" : "none";
    registerForm.style.display = tab === "register" ? "flex" : "none";
    if (pinSection) {
        pinSection.style.display = "none";
    }
}

// Alias funksiya - HTML da switchTab ishlatilgan
function switchTab(tab) {
    switchAuthTab(tab);
}

// ── LOGIN ──
async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value;

    try {
        const res = await api.post("/auth/login/", { username, password });
        if (res.ok) {
            const data = await res.json();
            setTokens(data.access, data.refresh);
            await fetchCurrentUser();
            closeModal("authModal");
            toast("Muvaffaqiyatli kirdingiz!", "success");
            goHome();
        } else {
            const err = await res.json();
            toast(err.detail || "Login xatolik!", "error");
        }
    } catch (e) {
        toast("Server bilan bog'lanib bo'lmadi", "error");
    }
}

// ── REGISTER (1-qadam: email yuborish) ──
async function handleRegister(e) {
    e.preventDefault();
    if (regUid) return; // allaqachon yuborilgan

    const username = document.getElementById("regUsername").value.trim();
    const email = document.getElementById("regEmail").value.trim();
    const password = document.getElementById("regPassword").value;
    const conform_password = document.getElementById("regConfirmPassword").value;

    if (password !== conform_password) {
        toast("Parollar mos kelmaydi!", "error");
        return;
    }

    try {
        const res = await api.post("/auth/registar/", { username, password, conform_password, email });
        const data = await res.json();
        if (res.ok) {
            regUid = data.uid;
            document.getElementById("pinSection").style.display = "block";
            toast("Emailingizga PIN kod yuborildi!", "success");
        } else {
            toast(data.message || JSON.stringify(data), "error");
        }
    } catch (e) {
        toast("Server bilan bog'lanib bo'lmadi", "error");
    }
}

// ── REGISTER (2-qadam: PIN tasdiqlash) ──
async function handlePinCheck() {
    const pincode = parseInt(document.getElementById("regPincode").value);
    if (!regUid || !pincode) {
        toast("PIN kodni kiriting", "error");
        return;
    }

    try {
        const res = await api.post("/auth/emailcheck/", { uid: regUid, pincode });
        if (res.ok) {
            const data = await res.json();
            setTokens(data.access, data.refresh);
            regUid = null;
            await fetchCurrentUser();
            closeModal("authModal");
            toast("Ro'yxatdan muvaffaqiyatli o'tdingiz!", "success");
            goHome();
        } else {
            const err = await res.json();
            toast(err.message || "PIN xato", "error");
        }
    } catch (e) {
        toast("Server bilan bog'lanib bo'lmadi", "error");
    }
}

// ── LOGOUT ──
async function handleLogout() {
    try {
        const refresh = getRefreshToken();
        if (refresh) {
            await api.post("/auth/logout/", { refresh });
        }
    } catch (e) { /* ignore */ }
    clearTokens();
    currentUser = null;
    updateAuthUI();
    toast("Tizimdan chiqdingiz", "info");
    // Seller sahifada bo'lsa auth ga, aks holda home ga
    if (window.location.pathname.startsWith("/seller")) {
        window.location.href = "/auth/";
    } else {
        goHome();
    }
}
