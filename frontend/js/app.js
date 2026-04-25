// ==============================
// 🌐 API CONFIG
// ==============================
const API = "http://127.0.0.1:5000";

// ORS KEY
const ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjdjN2EzNGU3MzhjZDRiY2E5ZGMxNzI5ZmFjOTI1NjVlIiwiaCI6Im11cm11cjY0In0=";

let map, routeLayer;
let startMarker, destMarker;
let poolCheckInterval = null;

// ==============================
// 🔐 FIXED AUTH HEADER
// ==============================
function getAuthHeader() {
  return {
    "Authorization": "Bearer " + localStorage.getItem("token"),
    "Content-Type": "application/json"
  };
}

// ==============================
// 🚀 NAVIGATION
// ==============================
function goTo(page) {
  document.body.style.opacity = "0";
  setTimeout(() => (window.location.href = page), 200);
}


// ==============================
// 🌍 INIT MAP
// ==============================
function initMap() {
  const mapEl = document.getElementById("map");
  if (!mapEl) return;

  map = L.map("map").setView([21.25, 81.63], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);

  map.on("click", (e) => {
    let { lat, lng } = e.latlng;

    if (!window.startLat) {
      setPickup(lat, lng);
    } else if (!window.destLat) {
      setDestination(lat, lng);
      drawRoute();
    } else {
      resetSelection();
    }
  });
}


// ==============================
// 📍 PICKUP
// ==============================
function setPickup(lat, lng) {
  window.startLat = lat;
  window.startLng = lng;

  if (startMarker) map.removeLayer(startMarker);

  startMarker = L.marker([lat, lng]).addTo(map);

  const el = document.getElementById("start");
  if (el) el.value = "Pickup Selected";
}


// ==============================
// 📍 DESTINATION
// ==============================
function setDestination(lat, lng) {
  window.destLat = lat;
  window.destLng = lng;

  if (destMarker) map.removeLayer(destMarker);

  destMarker = L.marker([lat, lng]).addTo(map);

  const el = document.getElementById("destination");
  if (el) el.value = "Destination Selected";
}


// ==============================
// 🔄 RESET
// ==============================
function resetSelection() {
  if (startMarker) map.removeLayer(startMarker);
  if (destMarker) map.removeLayer(destMarker);
  if (routeLayer) map.removeLayer(routeLayer);

  window.startLat = null;
  window.destLat = null;

  document.getElementById("start").value = "";
  document.getElementById("destination").value = "";

  showToast("🔄 Selection Reset");
}


// ==============================
// 🔎 SEARCH LOCATION
// ==============================
async function searchLocation(query, dropdownId, isPickup) {
  if (!query || query.length < 3) return;

  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${query}&limit=5`
    );

    const data = await res.json();
    const dropdown = document.getElementById(dropdownId);

    if (!dropdown) return;

    dropdown.innerHTML = "";

    data.forEach((place) => {
      const div = document.createElement("div");
      div.className = "dropdown-item";
      div.innerText = place.display_name;

      div.onclick = () => {
        const lat = parseFloat(place.lat);
        const lng = parseFloat(place.lon);

        map.setView([lat, lng], 14);

        if (isPickup) setPickup(lat, lng);
        else setDestination(lat, lng);

        dropdown.innerHTML = "";
      };

      dropdown.appendChild(div);
    });

  } catch (err) {
    console.log("Search error:", err);
  }
}


// ==============================
// 🛣 ROUTE (OPENROUTESERVICE)
// ==============================
async function drawRoute() {

  if (!window.startLat || !window.destLat) return;

  try {
    const res = await fetch(
      "https://api.openrouteservice.org/v2/directions/driving-car/geojson",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${ORS_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          coordinates: [
            [window.startLng, window.startLat],
            [window.destLng, window.destLat],
          ],
        }),
      }
    );

    const data = await res.json();

    if (routeLayer) map.removeLayer(routeLayer);

    routeLayer = L.geoJSON(data).addTo(map);

  } catch (err) {
    showToast("Route error ❌");
  }
}



// ==============================
// 🚲 ADD RIDE
// ==============================
async function addRide() {

  if (!window.startLat || !window.destLat) {
    showToast("Select pickup & destination ❌");
    return;
  }

  showLoader(true);

  try {
    const res = await fetch(API + "/add_ride", {
      method: "POST",
      headers: getAuthHeader(),
      body: JSON.stringify({
        start: document.getElementById("start")?.value,
        destination: document.getElementById("destination")?.value,
        start_lat: window.startLat,
        start_lng: window.startLng,
        dest_lat: window.destLat,
        dest_lng: window.destLng,
        time: document.getElementById("time")?.value,
      }),
    });

    const data = await res.json();

    showToast(data.message || "🎉 Ride Booked Successfully!");

    // ✅ IF MATCH FOUND → DIRECT GO ACTIVE RIDE
    if (data.match_found) {
      showToast("⚡ Instant Match Found!");
      setTimeout(() => goTo("active_ride.html"), 1200);
    } else {
      startAutoMatch();
    }

  } catch (err) {
    console.log(err);
    showToast("Error creating ride ❌");
  }

  showLoader(false);
}



// ==============================
// 🔄 AUTO MATCH (FIXED ENDPOINT)
// ==============================
function startAutoMatch() {

  if (poolCheckInterval) clearInterval(poolCheckInterval);

  poolCheckInterval = setInterval(async () => {

    try {

      const res = await fetch(API + "/check_match", {
        headers: getAuthHeader()
      });

      const data = await res.json();

      if (data.match_found) {
        clearInterval(poolCheckInterval);

        showToast("🎉 Match Found!");

        setTimeout(() => {
          goTo("active_ride.html");
        }, 1200);
      }

    } catch (err) {
      console.log(err);
    }

  }, 3000);
}




// ==============================
// 🔔 TOAST
// ==============================
function showToast(msg) {
  const t = document.getElementById("toast");
  if (!t) return;

  t.innerText = msg;
  t.style.display = "block";

  setTimeout(() => {
    t.style.display = "none";
  }, 2500);
}

// ==============================
// ⏳ LOADER
// ==============================
function showLoader(show) {
  const l = document.getElementById("loader");
  if (!l) return;

  l.style.display = show ? "block" : "none";
}


// ==============================
// 📱 MOBILE MENU
// ==============================
function toggleMenu() {
  const menu = document.getElementById("mobileMenu");
  if (!menu) return;

  menu.style.display = menu.style.display === "block" ? "none" : "block";
}


// ==============================
// INIT
// ==============================
document.addEventListener("DOMContentLoaded", () => {
  initMap();

  const start = document.getElementById("start");
  const dest = document.getElementById("destination");

  if (start) {
    start.addEventListener("input", (e) =>
      searchLocation(e.target.value, "pickupDropdown", true)
    );
  }

  if (dest) {
    dest.addEventListener("input", (e) =>
      searchLocation(e.target.value, "dropDropdown", false)
    );
  }
});