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
    const pinStep = document.getElementById("pinStep");
    const tabLogin = document.getElementById("tabLogin");
    const tabRegister = document.getElementById("tabRegister");
    
    // Null tekshiruvi - barcha elementlar
    if (!loginForm || !registerForm) {
        console.error('Forms not found:', {
            loginForm: !!loginForm,
            registerForm: !!registerForm,
            pinStep: !!pinStep
        });
        return;
    }
    
    if (!tabLogin || !tabRegister) {
        console.error('Tabs not found');
        return;
    }
    
    // Tab aktivligini o'zgartirish
    if (tab === "login") {
        tabLogin.classList.add("active");
        tabRegister.classList.remove("active");
    } else {
        tabLogin.classList.remove("active");
        tabRegister.classList.add("active");
    }
    
    // Form ko'rsatish/yashirish
    loginForm.style.display = tab === "login" ? "flex" : "none";
    registerForm.style.display = tab === "register" ? "flex" : "none";
    
    // PIN step yashirish
    if (pinStep) {
        pinStep.style.display = "none";
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

    if (!username || !password) {
        toast("Barcha maydonlarni to'ldiring", "error");
        return;
    }

    try {
        const res = await apiFetch("/auth/login/", {
            method: "POST",
            body: JSON.stringify({ username, password })
        });
        
        if (res.ok) {
            const data = await res.json();
            setTokens(data.access, data.refresh);
            await fetchCurrentUser();
            toast("Muvaffaqiyatli kirdingiz!", "success");
            window.location.href = "/";
        } else {
            const err = await res.json();
            toast(err.detail || err.message || "Login xatolik!", "error");
        }
    } catch (e) {
        console.error("Login error:", e);
        toast("Server bilan bog'lanib bo'lmadi", "error");
    }
}

// Alias - HTML da authLogin ishlatilgan
function authLogin(e) {
    return handleLogin(e);
}

// ── REGISTER (1-qadam: email yuborish) ──
async function handleRegister(e) {
    e.preventDefault();
    
    const username = document.getElementById("regUsername").value.trim();
    const email = document.getElementById("regEmail").value.trim();
    const password = document.getElementById("regPassword").value;
    const conform_password = document.getElementById("regConfirmPassword").value;

    // Validatsiya
    if (!username || !email || !password || !conform_password) {
        toast("Barcha maydonlarni to'ldiring", "error");
        return;
    }

    if (password !== conform_password) {
        toast("Parollar mos kelmaydi!", "error");
        return;
    }

    if (password.length < 8) {
        toast("Parol kamida 8 ta belgidan iborat bo'lishi kerak", "error");
        return;
    }

    try {
        const res = await apiFetch("/auth/registar/", {
            method: "POST",
            body: JSON.stringify({ username, email, password, conform_password })
        });
        
        const data = await res.json();
        
        if (res.ok) {
            regUid = data.uid;
            
            // PIN step ko'rsatish
            const registerForm = document.getElementById("registerForm");
            const pinStep = document.getElementById("pinStep");
            const pinEmailDisplay = document.getElementById("pinEmailDisplay");
            
            if (registerForm) registerForm.style.display = "none";
            if (pinStep) pinStep.style.display = "flex";
            if (pinEmailDisplay) pinEmailDisplay.textContent = email;
            
            toast("Emailingizga PIN kod yuborildi!", "success");
        } else {
            // Xatoliklarni ko'rsatish
            if (data.username) {
                toast("Username: " + (Array.isArray(data.username) ? data.username[0] : data.username), "error");
            } else if (data.email) {
                toast("Email: " + (Array.isArray(data.email) ? data.email[0] : data.email), "error");
            } else if (data.password) {
                toast("Parol: " + (Array.isArray(data.password) ? data.password[0] : data.password), "error");
            } else {
                toast(data.message || data.detail || "Ro'yxatdan o'tishda xatolik", "error");
            }
        }
    } catch (e) {
        console.error("Register error:", e);
        toast("Server bilan bog'lanib bo'lmadi", "error");
    }
}

// Alias - HTML da authRegister ishlatilgan
function authRegister(e) {
    return handleRegister(e);
}

// ── REGISTER (2-qadam: PIN tasdiqlash) ──
async function handlePinCheck() {
    const pincodeInput = document.getElementById("regPincode");
    if (!pincodeInput) {
        toast("PIN input topilmadi", "error");
        return;
    }
    
    const pincode = parseInt(pincodeInput.value);
    
    if (!regUid) {
        toast("Avval ro'yxatdan o'ting", "error");
        return;
    }
    
    if (!pincode || isNaN(pincode)) {
        toast("PIN kodni kiriting", "error");
        return;
    }

    try {
        const res = await apiFetch("/auth/emailcheck/", {
            method: "POST",
            body: JSON.stringify({ uid: regUid, pincode })
        });
        
        const data = await res.json();
        
        if (res.ok) {
            setTokens(data.access, data.refresh);
            regUid = null;
            await fetchCurrentUser();
            toast("Ro'yxatdan muvaffaqiyatli o'tdingiz!", "success");
            window.location.href = "/";
        } else {
            toast(data.message || data.detail || "PIN xato", "error");
        }
    } catch (e) {
        console.error("PIN check error:", e);
        toast("Server bilan bog'lanib bo'lmadi", "error");
    }
}

// Alias - HTML da authPinCheck ishlatilgan
function authPinCheck() {
    return handlePinCheck();
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

// ── GOOGLE AUTH ──
async function googleAuth() {
    console.log("Google auth started...");
    try {
        const res = await apiFetch("/auth/google/", {
            method: "POST"
        });
        
        console.log("Response status:", res.status);
        const data = await res.json();
        console.log("Response data:", data);
        
        if (res.ok) {
            if (data.google_auth_link) {
                console.log("Redirecting to:", data.google_auth_link);
                window.location.href = data.google_auth_link;
            } else {
                toast("Google auth link topilmadi", "error");
            }
        } else {
            toast(data.detail || data.message || "Google auth xatoligi", "error");
        }
    } catch (e) {
        console.error("Google auth error:", e);
        toast("Server bilan bog'lanib bo'lmadi", "error");
    }
}

// ── TOGGLE PASSWORD VISIBILITY ──
function togglePassword(inputId, btn) {
    const inp = document.getElementById(inputId);
    const icon = btn.querySelector("i");
    if (!inp || !icon) return;
    
    if (inp.type === "password") {
        inp.type = "text";
        icon.classList.replace("fa-eye", "fa-eye-slash");
    } else {
        inp.type = "password";
        icon.classList.replace("fa-eye-slash", "fa-eye");
    }
}
