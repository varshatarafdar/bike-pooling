// ==============================
// 🌐 BASE CONFIG
// ==============================
const API_BASE = "http://127.0.0.1:5000";


// ==============================
// 🔐 TOKEN
// ==============================
function getToken() {
  return localStorage.getItem("token");
}


// ==============================
// 🔥 CORE REQUEST FUNCTION
// ==============================
async function apiRequest(endpoint, method = "GET", body = null) {

  let headers = {
    "Content-Type": "application/json"
  };

  // attach token if exists
  let token = getToken();
  if (token) {
    headers["Authorization"] = token;
  }

  try {

    let res = await fetch(API_BASE + endpoint, {
      method,
      headers,
      body: body ? JSON.stringify(body) : null
    });

    let data = await res.json();

    // 🔥 handle errors
    if (!res.ok) {
      throw new Error(data.error || "Request failed");
    }

    return data;

  } catch (err) {
    console.error(err);
    showToast(err.message || "⚠️ Network error");
    return null;
  }
}


// ==============================
// 🔐 AUTH APIs
// ==============================
async function loginAPI(email, password) {
  return await apiRequest("/login", "POST", { email, password });
}

async function registerAPI(userData) {
  return await apiRequest("/register", "POST", userData);
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