// ==============================
// 🌐 API CONFIG
// ==============================
const API = "http://127.0.0.1:5000";
const ORS_API_KEY =
  "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjdjN2EzNGU3MzhjZDRiY2E5ZGMxNzI5ZmFjOTI1NjVlIiwiaCI6Im11cm11cjY0In0=";

let map, routeLayer;
let startMarker, destMarker;

let poolCheckInterval = null;


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
  if (!document.getElementById("map")) return;

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
// 📍 LOCATION SETTERS
// ==============================
function setPickup(lat, lng) {
  window.startLat = lat;
  window.startLng = lng;

  if (startMarker) map.removeLayer(startMarker);
  startMarker = L.marker([lat, lng]).addTo(map);

  document.getElementById("start").value = "Pickup Selected";
}

function setDestination(lat, lng) {
  window.destLat = lat;
  window.destLng = lng;

  if (destMarker) map.removeLayer(destMarker);
  destMarker = L.marker([lat, lng]).addTo(map);

  document.getElementById("destination").value = "Destination Selected";
}


// ==============================
// 🔎 SEARCH (NOMINATIM)
// ==============================
async function searchLocation(query, dropdownId, isPickup) {

  if (!query || query.length < 3) return;

  let res = await fetch(
    `https://nominatim.openstreetmap.org/search?format=json&q=${query}&limit=5`
  );

  let data = await res.json();
  let dropdown = document.getElementById(dropdownId);
  dropdown.innerHTML = "";

  data.forEach((place) => {

    let div = document.createElement("div");
    div.className = "dropdown-item";
    div.innerText = place.display_name;

    div.onclick = () => {

      let lat = parseFloat(place.lat);
      let lng = parseFloat(place.lon);

      map.setView([lat, lng], 14);

      if (isPickup) {
        setPickup(lat, lng);
      } else {
        setDestination(lat, lng);
        drawRoute();
      }

      dropdown.innerHTML = "";
    };

    dropdown.appendChild(div);
  });
}


// ==============================
// 🛣️ ROUTE (ORS)
// ==============================
async function drawRoute() {

  if (!window.startLat || !window.destLat) return;

  try {

    let res = await fetch(
      "https://api.openrouteservice.org/v2/directions/driving-car/geojson",
      {
        method: "POST",
        headers: {
          Authorization: ORS_API_KEY,
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

    let data = await res.json();

    if (routeLayer) map.removeLayer(routeLayer);
    routeLayer = L.geoJSON(data).addTo(map);

  } catch {
    showToast("Route error ❌");
  }
}


// ==============================
// 🚲 ADD RIDE + AUTO MATCH
// ==============================
async function addRide() {

  if (!window.startLat || !window.destLat) {
    showToast("Select pickup & destination ❌");
    return;
  }

  showLoader(true);

  try {

    let res = await fetch(API + "/add_ride", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: localStorage.getItem("token"),
      },
      body: JSON.stringify({
        start: document.getElementById("start").value,
        destination: document.getElementById("destination").value,
        start_lat: window.startLat,
        start_lng: window.startLng,
        dest_lat: window.destLat,
        dest_lng: window.destLng,
        time: document.getElementById("time").value,
      }),
    });

    let data = await res.json();

    showToast("🔍 Searching for match...");

    startAutoMatch();

  } catch {
    showToast("Error creating ride ❌");
  }

  showLoader(false);
}


// ==============================
// 🔄 AUTO MATCH POLLING
// ==============================
function startAutoMatch() {

  if (poolCheckInterval) clearInterval(poolCheckInterval);

  poolCheckInterval = setInterval(async () => {

    let res = await fetch(API + "/check_match", {
      headers: {
        Authorization: localStorage.getItem("token"),
      },
    });

    let data = await res.json();

    if (data.match_found) {

      clearInterval(poolCheckInterval);

      showToast("🎉 Match Found!");

      setTimeout(() => {
        goTo("active_ride.html");
      }, 1200);
    }

  }, 3000);
}


// ==============================
// 🔔 UI HELPERS
// ==============================
function showToast(msg) {
  let t = document.getElementById("toast");
  if (!t) return;
  t.innerText = msg;
  t.style.display = "block";

  setTimeout(() => (t.style.display = "none"), 2500);
}

function showLoader(show) {
  let l = document.getElementById("loader");
  if (!l) return;
  l.style.display = show ? "block" : "none";
}


// ==============================
// INIT
// ==============================
document.addEventListener("DOMContentLoaded", () => {
  initMap();

  let start = document.getElementById("start");
  let dest = document.getElementById("destination");

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