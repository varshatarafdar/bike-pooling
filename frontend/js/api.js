// ==============================
// 🌐 BASE CONFIG
// ==============================
const API_BASE = "http://127.0.0.1:5000";

// ==============================
// 🔐 TOKEN HELPERS
// ==============================
function getToken() {
  return localStorage.getItem("token");
}

function setToken(token) {
  localStorage.setItem("token", token);
}

function logout() {
  localStorage.clear();
  window.location.href = "login.html";
}

// ==============================
// 🍞 SAFE TOAST (fallback)
// ==============================
function safeToast(msg) {
  if (typeof showToast === "function") {
    showToast(msg);
  } else {
    alert(msg);
  }
}

// ==============================
// 🔥 CORE REQUEST FUNCTION
// ==============================
async function apiRequest(endpoint, method = "GET", body = null) {

  let headers = {
    "Content-Type": "application/json"
  };

  let token = getToken();

  if (token) {
    headers["Authorization"] = "Bearer " + token;  // ✅ FIXED
  }

  try {

    let res = await fetch(API_BASE + endpoint, {
      method,
      headers,
      body: body ? JSON.stringify(body) : null
    });

    let data = await res.json();

    // 🔐 Handle unauthorized
    if (res.status === 401) {
      safeToast("Session expired, please login again");
      logout();
      return null;
    }

    // 🔥 Handle API errors
    if (!data.status) {
      throw new Error(data.message || "Request failed");
    }

    return data;

  } catch (err) {
    console.error("API ERROR:", err);
    safeToast(err.message || "⚠️ Network error");
    return null;
  }
}

// ==============================
// 🔐 AUTH APIs
// ==============================
async function loginAPI(email, password) {
  return await apiRequest("/auth/login", "POST", { email, password });
}

async function registerAPI(userData) {
  return await apiRequest("/auth/register", "POST", userData);
}

// ==============================
// 🚲 RIDE APIs
// ==============================
async function createRideAPI(rideData) {
  return await apiRequest("/add_ride", "POST", rideData);
}

async function checkMatchAPI() {
  return await apiRequest("/check_match");
}

async function getMatchesAPI() {
  return await apiRequest("/my_matches");
}

// ==============================
// 🤝 BOOKING APIs
// ==============================
async function getActiveBookingAPI() {
  return await apiRequest("/active_booking");
}

async function createBookingAPI(data) {
  return await apiRequest("/create_pool", "POST", data);
}

// ==============================
// 👤 USER APIs
// ==============================
async function getProfileAPI() {
  return await apiRequest("/profile");
}

async function updateProfileAPI(data) {
  return await apiRequest("/profile", "PUT", data);
}

async function deleteAccountAPI() {
  return await apiRequest("/profile", "DELETE");
}