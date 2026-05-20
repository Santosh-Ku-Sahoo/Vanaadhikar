// API Configuration
const API_BASE = 'http://127.0.0.1:5000/api';

// Global Application State
let state = {
  villages: [],
  stats: {},
  activeVillage: null,
  activeTab: 'webgis-tab',
  dssThresholds: {
    water_threshold: 0.40,
    infra_threshold: 0.50,
    land_threshold: 2.0
  }
};

// Global Chart instances
let charts = {};

// Mock Scanned Documents content for AI Digitizer
const mockDocuments = {
  doc1: {
    name: "ramesh_baiga_ifr.txt",
    size: "410 bytes",
    content: `CLAIM FOR INDIVIDUAL FOREST RIGHTS
----------------------------------
Claimant Name: Ramesh Baiga
Tribal Group: PVTG - Baiga community
State: Madhya Pradesh, District: Mandla, Village: Kanha Basti
Claim Details: Requesting ownership right over ancestral agricultural land.
Plot coordinates: Lat 22.3312, Lng 80.6115
Acres Claimed: 4.2 Acres
Status: Under cultivation for 3 generations (Maize & Minor Forest Produce).`
  },
  doc2: {
    name: "savitri_baiga_ifr.txt",
    size: "395 bytes",
    content: `INDIVIDUAL FOREST CLAIM APPLICATION
-----------------------------------
Applicant: Savitri Baiga
Community Category: Baiga PVTG
Location: Village Kanha Basti, Mandla District, MP State.
Acreage under claim: 3.0 Acres of forest margin farmland.
GPS Position: Lat 22.3308, Lng 80.6085
Documents attached: Joint signature list of Gram Sabha, verification report.`
  },
  doc3: {
    name: "gandachara_cfr.txt",
    size: "485 bytes",
    content: `COMMUNITY FOREST RESOURCE RIGHTS CLAIM
--------------------------------------
Claimant: Ganda Chara Joint Forest Committee
Representing: Tripuri tribal group
State: Tripura, District: Dhalai, Village: Ganda Chara
Type of Claim: CFR (Community Forest Resource rights)
Total Resource Area: 150.0 Acres of bamboo and deciduous forest zone.
Coordinates Boundary Center: Lat 23.4845, Lng 91.8795
Rights demanded: Collection of Tendu, Bamboo shoots, and protection rights.`
  },
  doc4: {
    name: "suresh_santhal_ifr.txt",
    size: "440 bytes",
    content: `OFFICE OF THE GRAM SABHA - INDIVIDUAL CLAIM
-------------------------------------------
Claim of: Suresh Santhal
Community Group: Santhal Tribe
State: Odisha, District: Mayurbhanj, Village: Similipal Pada
Property Description: Homestead and backyard horticultural orchard plot.
Area: 3.8 Acres
GPS Coordinates: Lat 21.9215, Lng 86.3512
Gram Sabha Recommendation: Recommended for verification. Cultivation verified.`
  },
  doc5: {
    name: "ram_gond_ifr.txt",
    size: "420 bytes",
    content: `FOREST DWELLERS LAND RIGHTS FORM
--------------------------------
Claimant: Ram Gond
Tribal Association: Gond Tribe
Location: Adilabad Pada village, Adilabad District, Telangana State.
Claim Type: IFR (Individual Forest Rights)
Assigned Parcel Size: 4.5 Acres of podu farming land.
Coordinates: Lat 19.6705, Lng 78.5312
Filing Date: March 2025.`
  }
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  initRouter();
  initMap();
  initTheme();
  loadData();
  initDigitizer();
  initSatelliteCV();
  initDSS();
});

// 1. Theme Toggle Logic
function initTheme() {
  const toggleBtn = document.getElementById('theme-toggle');
  toggleBtn.addEventListener('click', () => {
    document.body.classList.toggle('dark-theme');
    document.body.classList.toggle('light-theme');
    
    const isDark = document.body.classList.contains('dark-theme');
    toggleBtn.innerHTML = isDark ? 
      `<i class="fa-solid fa-sun"></i> <span>Light Mode</span>` : 
      `<i class="fa-solid fa-moon"></i> <span>Dark Mode</span>`;
  });
}

// 2. Tab Routing
function initRouter() {
  const menuItems = document.querySelectorAll('.menu-item');
  menuItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      
      // Update sidebar visual active state
      menuItems.forEach(mi => mi.classList.remove('active'));
      item.classList.add('active');
      
      // Switch active tab pane
      const tabId = item.getAttribute('data-tab');
      state.activeTab = tabId;
      
      document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
      });
      document.getElementById(tabId).classList.add('active');
      
      // Update top header labels based on tab
      updateHeaderLabels(tabId);
      
      // Re-trigger layout refreshes if needed (like Map resizing)
      if (tabId === 'webgis-tab') {
        setTimeout(() => map.invalidateSize(), 100);
      } else if (tabId === 'analytics-tab') {
        renderCharts();
      }
    });
  });
}

function updateHeaderLabels(tabId) {
  const title = document.getElementById('page-title');
  const subtitle = document.getElementById('page-subtitle');
  
  switch(tabId) {
    case 'webgis-tab':
      title.innerText = "WebGIS Portal";
      subtitle.innerText = "Interactive monitoring of Forest Rights Act (FRA) implementation";
      break;
    case 'analytics-tab':
      title.innerText = "Analytics & Progress";
      subtitle.innerText = "FRA registration, metrics and assets distribution details";
      break;
    case 'digitizer-tab':
      title.innerText = "AI Claim Digitizer";
      subtitle.innerText = "Extracting Named Entities from scanned legacy forest rights pattas";
      break;
    case 'satellite-tab':
      title.innerText = "Satellite Asset Mapping";
      subtitle.innerText = "Remote sensing asset detection and forest cover tracking";
      break;
    case 'dss-tab':
      title.innerText = "DSS Scheme Layering";
      subtitle.innerText = "Multi-ministry policy recommendation engine for FRA patta holders";
      break;
  }
}

// 3. WebGIS Map Variables & Setup
let map;
let mapLayers = {
  villages: L.layerGroup(),
  boundaries: L.layerGroup(),
  assets: L.layerGroup()
};

function initMap() {
  // Center map on central India
  map = L.map('map', {
    center: [20.5937, 78.9629],
    zoom: 5.5,
    zoomControl: true
  });
  
  // Add OpenStreetMap tile layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  // Add layers to map
  mapLayers.boundaries.addTo(map);
  mapLayers.villages.addTo(map);
  mapLayers.assets.addTo(map);

  // Add Interactive Layer Toggle Controls
  const overlays = {
    "Village Boundaries": mapLayers.boundaries,
    "Village Centers": mapLayers.villages,
    "Satellite Mapped Assets": mapLayers.assets
  };
  L.control.layers(null, overlays, { collapsed: false }).addTo(map);
  
  // Set up event listeners for filters
  document.getElementById('map-state-filter').addEventListener('change', applyMapFilters);
  document.getElementById('map-district-filter').addEventListener('input', applyMapFilters);
  document.getElementById('map-tribal-filter').addEventListener('change', applyMapFilters);
  document.getElementById('map-type-filter').addEventListener('change', applyMapFilters);
  document.getElementById('map-status-filter').addEventListener('change', applyMapFilters);
  document.getElementById('btn-reset-filters').addEventListener('click', resetMapFilters);
}

// 4. API Data Loading
async function loadData() {
  try {
    // Fetch statistics
    const statsRes = await fetch(`${API_BASE}/stats`);
    state.stats = await statsRes.json();
    updateHeaderStats();

    // Fetch villages
    const vilRes = await fetch(`${API_BASE}/villages`);
    state.villages = await vilRes.json();
    
    // Render on Map
    renderMapData(state.villages);
    
    // Populate Sat Village Select
    populateVillageSelectors();
    
  } catch (error) {
    console.error("Error loading data from backend:", error);
    // Display offline/error notification
    document.querySelector('.connection-status').innerHTML = `
      <span class="status-dot online" style="background-color: var(--danger); box-shadow: 0 0 8px var(--danger);"></span>
      <span class="status-text">Backend Offline</span>
    `;
  }
}

function updateHeaderStats() {
  if (state.stats) {
    document.getElementById('header-total-claims').innerText = state.stats.total_claims || 0;
    document.getElementById('header-total-area').innerText = `${state.stats.total_area_acres || 0} ac`;
  }
}

function populateVillageSelectors() {
  const satSelect = document.getElementById('sat-village-select');
  if (!satSelect) return;
  
  satSelect.innerHTML = "";
  state.villages.forEach(v => {
    const opt = document.createElement('option');
    opt.value = v.id;
    opt.innerText = `${v.name} (${v.state_name})`;
    satSelect.appendChild(opt);
  });
  
  // Trigger initial selection load
  if (state.villages.length > 0) {
    loadSatelliteVillage(state.villages[0].id);
  }
}

// 5. WebGIS Map Rendering & Filter Logic
function renderMapData(villages) {
  // Clear old layers
  mapLayers.villages.clearLayers();
  mapLayers.boundaries.clearLayers();
  mapLayers.assets.clearLayers();
  
  villages.forEach(v => {
    // Determine overall village status color based on its claims
    let statusColor = "var(--text-muted)";
    let hasVerified = v.claims.some(c => c.status === 'Verified');
    let hasPending = v.claims.some(c => c.status === 'Pending');
    let hasRejected = v.claims.some(c => c.status === 'Rejected');
    
    if (hasVerified) {
      statusColor = "var(--primary)"; // Green
    } else if (hasPending) {
      statusColor = "var(--warning)"; // Amber
    } else if (hasRejected) {
      statusColor = "var(--danger)"; // Red
    }
    
    // 1. Draw boundary Polygon
    if (v.boundary_geojson && v.boundary_geojson.geometry) {
      const boundaryLayer = L.geoJSON(v.boundary_geojson, {
        style: {
          color: statusColor,
          weight: 2,
          opacity: 0.8,
          fillColor: statusColor,
          fillOpacity: 0.15
        }
      });
      
      boundaryLayer.on('click', () => selectVillage(v));
      boundaryLayer.addTo(mapLayers.boundaries);
    }
    
    // 2. Draw Marker
    const marker = L.circleMarker([v.latitude, v.longitude], {
      radius: 8,
      fillColor: statusColor,
      color: "#ffffff",
      weight: 1.5,
      opacity: 1,
      fillOpacity: 0.9
    });
    
    marker.bindPopup(`
      <div class="map-popup">
        <h4>${v.name}</h4>
        <p><strong>State:</strong> ${v.state_name}</p>
        <p><strong>District:</strong> ${v.district_name}</p>
        <p><strong>Tribal Group:</strong> ${v.tribal_group}</p>
        <p><strong>Claims:</strong> ${v.claims.length} (Water Idx: ${v.water_index})</p>
      </div>
    `);
    
    marker.on('click', () => selectVillage(v));
    marker.addTo(mapLayers.villages);
    
    // 3. Draw Assets if village is selected
    if (state.activeVillage && state.activeVillage.id === v.id) {
      v.assets.forEach(asset => {
        if (asset.coordinates_geojson && asset.coordinates_geojson.geometry) {
          const coords = asset.coordinates_geojson.geometry.coordinates;
          // GeoJSON is [lng, lat]
          let color = "#10b981"; // default forest
          if (asset.asset_type === 'Pond') color = "#0ea5e9";
          else if (asset.asset_type === 'Agricultural Farm') color = "#fbbf24";
          else if (asset.asset_type === 'Homestead') color = "#a855f7";
          
          const assetMarker = L.circleMarker([coords[1], coords[0]], {
            radius: 5,
            fillColor: color,
            color: "#ffffff",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.85
          });
          
          assetMarker.bindPopup(`<b>${asset.asset_type}</b><br>Detected Area/Count: ${asset.count_or_area} ac`);
          assetMarker.addTo(mapLayers.assets);
        }
      });
    }
  });
}

function selectVillage(v) {
  state.activeVillage = v;
  
  // Center map on selected village
  map.setView([v.latitude, v.longitude], 13);
  
  // Show Sidebar Details Card
  document.getElementById('village-details-card').querySelector('.empty-selection-state').classList.add('d-none');
  const content = document.getElementById('village-details-content');
  content.classList.remove('d-none');
  
  // Fill details
  document.getElementById('v-detail-state').innerText = v.state_name;
  document.getElementById('v-detail-name').innerText = v.name;
  document.getElementById('v-detail-district').innerText = v.district_name;
  
  // Water Progress Bar
  const waterPct = v.water_index * 100;
  document.getElementById('v-detail-water-bar').style.width = `${waterPct}%`;
  document.getElementById('v-detail-water-val').innerText = v.water_index.toFixed(2);
  
  // Forest Progress Bar
  document.getElementById('v-detail-forest-bar').style.width = `${v.forest_cover_percentage}%`;
  document.getElementById('v-detail-forest-val').innerText = `${v.forest_cover_percentage.toFixed(1)}%`;
  
  // Infrastructure Progress Bar
  const infraPct = v.infrastructure_index * 100;
  document.getElementById('v-detail-infra-bar').style.width = `${infraPct}%`;
  document.getElementById('v-detail-infra-val').innerText = v.infrastructure_index.toFixed(2);
  
  // Render Claims list
  const claimsList = document.getElementById('v-detail-claims-list');
  claimsList.innerHTML = "";
  document.getElementById('v-detail-claims-count').innerText = v.claims.length;
  
  if (v.claims.length === 0) {
    claimsList.innerHTML = `<div class="log-line text-muted">No claims filed.</div>`;
  } else {
    v.claims.forEach(c => {
      const strip = document.createElement('div');
      strip.className = 'claim-strip';
      strip.innerHTML = `
        <div class="claim-strip-top">
          <span class="claimant-name">${c.claimant_name}</span>
          <span class="claim-status-dot ${c.status.toLowerCase()}">${c.status}</span>
        </div>
        <div class="claim-strip-bottom">
          <span>Type: <b>${c.claim_type}</b></span>
          <span>Area: <b>${c.area_acres} ac</b></span>
        </div>
      `;
      claimsList.appendChild(strip);
    });
  }
  
  // Render Assets list
  const assetsList = document.getElementById('v-detail-assets-list');
  assetsList.innerHTML = "";
  document.getElementById('v-detail-assets-count').innerText = v.assets.length;
  
  if (v.assets.length === 0) {
    assetsList.innerHTML = `<div class="log-line text-muted">No remote-sensing assets mapped. Select "Satellite Asset Map" tab to scan.</div>`;
  } else {
    v.assets.forEach(a => {
      const typeClass = a.asset_type.split(' ')[0].toLowerCase();
      let icon = "fa-tree";
      if (a.asset_type === 'Pond') icon = "fa-water";
      else if (a.asset_type === 'Agricultural Farm') icon = "fa-wheat-awn";
      else if (a.asset_type === 'Homestead') icon = "fa-house-chimney";
      
      const strip = document.createElement('div');
      strip.className = 'asset-strip';
      strip.innerHTML = `
        <div class="asset-icon-box ${typeClass}">
          <i class="fa-solid ${icon}"></i>
        </div>
        <div class="asset-info">
          <span class="name">${a.asset_type}</span>
          <span class="detail">Cover area: ${a.count_or_area} acres</span>
        </div>
      `;
      assetsList.appendChild(strip);
    });
  }
  
  // Re-draw map markers to overlay selected village assets
  renderMapData(state.villages);
}

function applyMapFilters() {
  const stateVal = document.getElementById('map-state-filter').value;
  const districtVal = document.getElementById('map-district-filter').value.trim().toLowerCase();
  const tribeVal = document.getElementById('map-tribal-filter').value;
  const typeVal = document.getElementById('map-type-filter').value;
  const statusVal = document.getElementById('map-status-filter').value;
  
  const filtered = state.villages.filter(v => {
    const matchesState = stateVal === "all" || v.state_name === stateVal;
    const matchesDistrict = districtVal === "" || v.district_name.toLowerCase().includes(districtVal);
    const matchesTribe = tribeVal === "all" || v.tribal_group === tribeVal;
    
    // Claim level filters
    let matchesType = typeVal === "all";
    let matchesStatus = statusVal === "all";
    
    if (v.claims.length === 0) {
      return matchesState && matchesDistrict && matchesTribe && matchesType && matchesStatus;
    }
    
    if (typeVal !== "all") {
      matchesType = v.claims.some(c => c.claim_type === typeVal);
    }
    
    if (statusVal !== "all") {
      matchesStatus = v.claims.some(c => c.status === statusVal);
    }
    
    return matchesState && matchesDistrict && matchesTribe && matchesType && matchesStatus;
  });
  
  renderMapData(filtered);
}

function resetMapFilters() {
  document.getElementById('map-state-filter').value = "all";
  document.getElementById('map-district-filter').value = "";
  document.getElementById('map-tribal-filter').value = "all";
  document.getElementById('map-type-filter').value = "all";
  document.getElementById('map-status-filter').value = "all";
  renderMapData(state.villages);
}

// 6. Analytics Charts (Chart.js)
function renderCharts() {
  if (!state.stats || !state.stats.state_breakdown) return;
  
  const stats = state.stats;
  
  // Destroy old charts to prevent duplicate canvases overlapping
  Object.keys(charts).forEach(key => {
    if (charts[key]) charts[key].destroy();
  });
  
  // Chart 1: State Breakdown Stacked Bar Chart
  const stateLabels = stats.state_breakdown.map(s => s.state);
  const verifiedData = stats.state_breakdown.map(s => s.verified_claims);
  const pendingData = stats.state_breakdown.map(s => s.pending_claims);
  const rejectedData = stats.state_breakdown.map(s => s.rejected_claims);
  
  const ctx1 = document.getElementById('stateClaimsChart').getContext('2d');
  charts.stateClaims = new Chart(ctx1, {
    type: 'bar',
    data: {
      labels: stateLabels,
      datasets: [
        {
          label: 'Verified Patta',
          data: verifiedData,
          backgroundColor: '#10b981',
          borderRadius: 4
        },
        {
          label: 'Pending Review',
          data: pendingData,
          backgroundColor: '#f59e0b',
          borderRadius: 4
        },
        {
          label: 'Rejected Claims',
          data: rejectedData,
          backgroundColor: '#ef4444',
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { stacked: true, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { stacked: true, grid: { color: 'rgba(255,255,255,0.05)' } }
      },
      plugins: {
        legend: { labels: { color: '#94a3b8' } }
      }
    }
  });
  
  // Chart 2: Claim Type Donut
  const ctx2 = document.getElementById('claimsTypeChart').getContext('2d');
  charts.claimType = new Chart(ctx2, {
    type: 'doughnut',
    data: {
      labels: ['Individual (IFR)', 'Community (CR)', 'Resource Rights (CFR)'],
      datasets: [{
        data: [stats.type_counts.IFR, stats.type_counts.CR, stats.type_counts.CFR],
        backgroundColor: ['#10b981', '#a855f7', '#0ea5e9'],
        borderWidth: 1,
        borderColor: 'rgba(0,0,0,0.5)'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#94a3b8', font: { size: 11 } }
        }
      }
    }
  });

  // Chart 3: Asset Density Bar Chart
  const ctx3 = document.getElementById('assetsDensityChart').getContext('2d');
  charts.assetsDensity = new Chart(ctx3, {
    type: 'bar',
    data: {
      labels: ['Farms', 'Ponds', 'Forest Resource', 'Homesteads'],
      datasets: [{
        label: 'Detected Assets Count',
        data: [
          stats.asset_counts['Agricultural Farm'] || 0,
          stats.asset_counts['Pond'] || 0,
          stats.asset_counts['Forest Resource'] || 0,
          stats.asset_counts['Homestead'] || 0
        ],
        backgroundColor: ['#fbbf24', '#38bdf8', '#10b981', '#a855f7'],
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: { grid: { color: 'rgba(255,255,255,0.05)' } }
      }
    }
  });
  
  // Render Comparison Table
  renderMetricsTable(stats.state_breakdown);
}

function renderMetricsTable(stateBreakdown) {
  const tbody = document.querySelector('#state-metrics-table tbody');
  tbody.innerHTML = "";
  
  stateBreakdown.forEach(s => {
    const progressRate = s.total_claims > 0 ? ((s.verified_claims / s.total_claims) * 100).toFixed(1) : 0;
    
    // Select color based on progress rate
    let progressColor = "var(--danger)";
    if (progressRate > 75) progressColor = "var(--primary)";
    else if (progressRate > 40) progressColor = "var(--warning)";
    
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${s.state}</strong></td>
      <td>${s.total_claims}</td>
      <td><span class="text-success">${s.verified_claims}</span></td>
      <td><span class="text-warning">${s.pending_claims}</span></td>
      <td><span class="text-danger">${s.rejected_claims}</span></td>
      <td>${s.total_area}</td>
      <td>${s.avg_water_index.toFixed(2)}</td>
      <td>${s.avg_forest_cover.toFixed(1)}%</td>
      <td>
        <div style="display: flex; align-items: center; gap: 8px;">
          <div class="progress-bar-wrapper" style="margin-top: 0; width: 60px; height: 6px; background-color: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden;">
            <div class="progress-bar" style="width: ${progressRate}%; height: 100%; background-color: ${progressColor};"></div>
          </div>
          <span style="font-size: 11px; font-weight: 700; color: ${progressColor};">${progressRate}%</span>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// 7. AI Digitizer Console simulation
function initDigitizer() {
  const select = document.getElementById('mock-doc-select');
  const runBtn = document.getElementById('btn-run-digitize');
  
  if (!select || !runBtn) return;
  
  // Update document viewer on select change
  select.addEventListener('change', () => {
    const docKey = select.value;
    const doc = mockDocuments[docKey];
    document.getElementById('selected-doc-name').innerText = doc.name;
    document.getElementById('selected-doc-content').innerText = doc.content;
  });
  
  // Trigger initial
  select.dispatchEvent(new Event('change'));
  
  runBtn.addEventListener('click', async () => {
    const docKey = select.value;
    const doc = mockDocuments[docKey];
    
    // Reset terminal output
    const terminal = document.getElementById('ocr-terminal');
    terminal.innerHTML = "";
    document.getElementById('ner-results-card').classList.add('d-none');
    
    // Simulate terminal log outputs
    const logs = [
      { text: "[INFO] Initializing Tesseract OCR v5.3 engine...", type: "muted", delay: 200 },
      { text: "[INFO] Reading input binary file buffer...", type: "muted", delay: 400 },
      { text: "[INFO] Performing document layout analysis (skew correction + thresholding)...", type: "muted", delay: 700 },
      { text: "[SUCCESS] OCR text extraction completed (confidence score: 98.4%).", type: "success", delay: 1000 },
      { text: "[INFO] Loading SpaCy Natural Language Processing model pipeline...", type: "muted", delay: 1300 },
      { text: "[INFO] Executing Named Entity Recognition (NER) models for FRA custom labels...", type: "info", delay: 1600 },
      { text: "[INFO] Identified ENTITIES: [CLAIMANT], [TRIBAL_GROUP], [VILLAGE], [COORDINATES], [AREA]...", type: "info", delay: 2000 },
      { text: "[INFO] Formatting standardized GeoJSON coordinates payload...", type: "muted", delay: 2300 },
      { text: "[INFO] Synchronizing with local SQLite backend system...", type: "muted", delay: 2600 }
    ];
    
    // Print logs sequentially
    for (let log of logs) {
      await new Promise(r => setTimeout(r, log.delay - (logs.indexOf(log) > 0 ? logs[logs.indexOf(log)-1].delay : 0)));
      const line = document.createElement('div');
      line.className = `log-line text-${log.type}`;
      line.innerText = log.text;
      terminal.appendChild(line);
      terminal.scrollTop = terminal.scrollHeight;
    }
    
    // Execute POST API call to Backend
    try {
      const response = await fetch(`${API_BASE}/digitize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_name: doc.name,
          text_content: doc.content
        })
      });
      const resData = await response.json();
      
      if (resData.success) {
        // Success terminal logs
        const finalLine = document.createElement('div');
        finalLine.className = 'log-line text-success';
        finalLine.innerText = `[SUCCESS] Database transaction committed. Claim ID: #${resData.claim_id}`;
        terminal.appendChild(finalLine);
        
        // Show NER tags grid
        document.getElementById('ner-results-card').classList.remove('d-none');
        document.getElementById('ner-claimant').innerText = resData.extracted_metadata.claimant_name;
        document.getElementById('ner-type').innerText = resData.extracted_metadata.claim_type;
        document.getElementById('ner-village').innerText = resData.extracted_metadata.village_name;
        document.getElementById('ner-area').innerText = resData.extracted_metadata.area_acres + " ac";
        document.getElementById('ner-tribal').innerText = resData.extracted_metadata.tribal_group;
        document.getElementById('ner-status').innerText = resData.extracted_metadata.status;
        
        // Reload all data to refresh map & statistics
        loadData();
      } else {
        throw new Error(resData.error || "Digitization failed");
      }
    } catch (err) {
      const errLine = document.createElement('div');
      errLine.className = 'log-line text-error';
      errLine.innerText = `[ERROR] Extraction pipeline failed: ${err.message}`;
      terminal.appendChild(errLine);
    }
  });
}

// 8. Remote Sensing Satellite CV Console
let landUseChartInstance = null;

function initSatelliteCV() {
  const select = document.getElementById('sat-village-select');
  const runCvBtn = document.getElementById('btn-trigger-cv');
  
  if (!select || !runCvBtn) return;
  
  select.addEventListener('change', () => {
    loadSatelliteVillage(select.value);
  });
  
  runCvBtn.addEventListener('click', async () => {
    const vId = select.value;
    runCvBtn.disabled = true;
    runCvBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Analyzing Satellite Imagery...`;
    
    // Add radar sweep visual effect to satellite window
    const satViewer = document.getElementById('sat-viewer-bg');
    const scanner = document.createElement('div');
    scanner.className = 'sat-hud-elements scanner-effect';
    scanner.style.background = 'linear-gradient(rgba(16, 185, 129, 0) 50%, rgba(16, 185, 129, 0.25) 100%)';
    scanner.style.height = '100%';
    scanner.style.width = '100%';
    scanner.style.position = 'absolute';
    scanner.style.top = '0';
    scanner.style.animation = 'scan-sweep 1.8s infinite linear';
    satViewer.appendChild(scanner);
    
    try {
      const response = await fetch(`${API_BASE}/detect-assets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ village_id: vId })
      });
      const data = await response.json();
      
      if (data.success) {
        // Wait 1.5 seconds to show visual effect
        await new Promise(r => setTimeout(r, 1500));
        
        // Remove scanner effect
        scanner.remove();
        
        // Reload village details and reload global data
        await loadData();
        loadSatelliteVillage(vId);
        
      } else {
        alert("Satellite CV mapping failed: " + data.error);
      }
    } catch (e) {
      console.error(e);
      alert("Error contacting CV backend.");
    } finally {
      runCvBtn.disabled = false;
      runCvBtn.innerHTML = `<i class="fa-solid fa-radar"></i> Run Satellite CV Asset Mapping`;
    }
  });
}

function loadSatelliteVillage(vId) {
  const vil = state.villages.find(v => v.id == vId);
  if (!vil) return;
  
  // Update HUD
  document.getElementById('sat-hud-coords').innerText = `Coords: ${vil.latitude.toFixed(4)}, ${vil.longitude.toFixed(4)}`;
  document.getElementById('sat-map-title').innerText = `${vil.name} Area Overlay`;
  
  document.getElementById('sat-stat-water').innerText = vil.water_index.toFixed(2);
  document.getElementById('sat-stat-forest').innerText = `${vil.forest_cover_percentage.toFixed(1)}%`;
  document.getElementById('sat-stat-infra').innerText = vil.infrastructure_index.toFixed(2);
  
  // Set simulated satellite background based on forest cover
  // We'll generate a visual representation using styling gradients to look like a satellite map
  const satViewer = document.getElementById('sat-viewer-bg');
  satViewer.innerHTML = ""; // Clear old asset markers
  
  let bgGradient = `radial-gradient(circle, #1e293b 0%, #0f172a 100%)`;
  if (vil.forest_cover_percentage > 70) {
    // Highly dense forest
    bgGradient = `radial-gradient(circle, #064e3b 10%, #022c22 100%)`;
  } else if (vil.forest_cover_percentage > 45) {
    bgGradient = `radial-gradient(circle, #0f5132 20%, #0f172a 90%)`;
  } else {
    bgGradient = `radial-gradient(circle, #2d3748 30%, #1a202c 100%)`;
  }
  satViewer.style.backgroundImage = 'none';
  satViewer.style.background = bgGradient;
  
  // Draw simulated asset boxes on the satellite view window
  vil.assets.forEach(asset => {
    if (asset.coordinates_geojson && asset.coordinates_geojson.geometry) {
      const coords = asset.coordinates_geojson.geometry.coordinates;
      // We will place asset box in the sat screen based on coordinates offset from village center
      const latDiff = coords[1] - vil.latitude;
      const lngDiff = coords[0] - vil.longitude;
      
      // Map offsets to percentages (max offset is approx 0.01)
      const topPct = 50 - (latDiff / 0.015) * 50;
      const leftPct = 50 + (lngDiff / 0.015) * 50;
      
      const typeClass = asset.asset_type.split(' ')[0].toLowerCase();
      let size = 15;
      if (asset.asset_type === 'Forest Resource') size = 45;
      else if (asset.asset_type === 'Pond') size = 20;
      
      const el = document.createElement('div');
      el.className = `sat-asset-marker ${typeClass}`;
      el.style.top = `${Math.max(10, Math.min(90, topPct))}%`;
      el.style.left = `${Math.max(10, Math.min(90, leftPct))}%`;
      el.style.height = `${size}px`;
      el.style.width = `${size}px`;
      el.title = `${asset.asset_type} (${asset.count_or_area} ac)`;
      satViewer.appendChild(el);
    }
  });
  
  // Update land use chart
  renderLandUseChart(vil);
}

function renderLandUseChart(vil) {
  // Aggregate assets
  const farmsArea = vil.assets.filter(a => a.asset_type === 'Agricultural Farm').reduce((sum, a) => sum + a.count_or_area, 0);
  const forestArea = vil.assets.filter(a => a.asset_type === 'Forest Resource').reduce((sum, a) => sum + a.count_or_area, 0);
  const pondArea = vil.assets.filter(a => a.asset_type === 'Pond').reduce((sum, a) => sum + a.count_or_area, 0);
  const homesteadArea = vil.assets.filter(a => a.asset_type === 'Homestead').reduce((sum, a) => sum + a.count_or_area, 0);
  
  const ctx = document.getElementById('landUseChart').getContext('2d');
  
  if (landUseChartInstance) {
    landUseChartInstance.destroy();
  }
  
  landUseChartInstance = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Forest Area', 'Farmland', 'Water Bodies', 'Homesteads'],
      datasets: [{
        data: [
          forestArea || 10, // dummy fallback values if no assets mapped
          farmsArea || 3, 
          pondArea || 1, 
          homesteadArea || 1
        ],
        backgroundColor: ['#10b981', '#fbbf24', '#38bdf8', '#a855f7'],
        borderWidth: 1,
        borderColor: 'rgba(0,0,0,0.5)'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#94a3b8', font: { size: 9 } }
        }
      }
    }
  });
}

// 9. Decision Support System (DSS) panel
function initDSS() {
  const waterSlider = document.getElementById('slider-water');
  const infraSlider = document.getElementById('slider-infra');
  const landSlider = document.getElementById('slider-land');
  const runDssBtn = document.getElementById('btn-recalculate-dss');
  
  if (!waterSlider || !infraSlider || !landSlider || !runDssBtn) return;
  
  // Real-time slider label updates
  waterSlider.addEventListener('input', () => {
    document.getElementById('val-water').innerText = parseFloat(waterSlider.value).toFixed(2);
  });
  infraSlider.addEventListener('input', () => {
    document.getElementById('val-infra').innerText = parseFloat(infraSlider.value).toFixed(2);
  });
  landSlider.addEventListener('input', () => {
    document.getElementById('val-land').innerText = parseFloat(landSlider.value).toFixed(1) + " ac";
  });
  
  runDssBtn.addEventListener('click', runDSSEngine);
  
  // Initial run once page loaded
  setTimeout(runDSSEngine, 1000);
}

async function runDSSEngine() {
  const wTh = document.getElementById('slider-water').value;
  const iTh = document.getElementById('slider-infra').value;
  const lTh = document.getElementById('slider-land').value;
  
  const runDssBtn = document.getElementById('btn-recalculate-dss');
  runDssBtn.disabled = true;
  runDssBtn.innerHTML = `<i class="fa-solid fa-arrows-spin fa-spin"></i> Running Engine Rules...`;
  
  try {
    const response = await fetch(`${API_BASE}/dss/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        water_threshold: wTh,
        infra_threshold: iTh,
        land_threshold: lTh
      })
    });
    
    const data = await response.json();
    if (data.success) {
      renderDSSResults(data);
    } else {
      alert("DSS evaluation failed: " + data.error);
    }
  } catch(e) {
    console.error(e);
    alert("Error communicating with DSS engine backend.");
  } finally {
    runDssBtn.disabled = false;
    runDssBtn.innerHTML = `<i class="fa-solid fa-arrows-spin"></i> Recalculate DSS Priorities`;
  }
}

function renderDSSResults(data) {
  const tbody = document.querySelector('#dss-results-table tbody');
  tbody.innerHTML = "";
  
  document.getElementById('dss-count-total').innerText = `${data.counts.total_recommendations} Recommendations Mapped`;
  
  if (data.recommendations.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No recommendations match the current threshold rules. Try increasing parameters.</td></tr>`;
    return;
  }
  
  data.recommendations.forEach(r => {
    // Style priority pill
    let prioClass = r.priority.toLowerCase();
    
    // Style Scheme Badge
    let schemeClass = r.scheme_name.split(' ')[0].toUpperCase();
    if (schemeClass.startsWith("JAL") || schemeClass.startsWith("JALJ")) schemeClass = "JJM";
    if (schemeClass.startsWith("MGNREGA")) schemeClass = "MGNREGA";
    
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="dss-priority-pill ${prioClass}">${r.priority}</span></td>
      <td><strong>${r.beneficiary_name}</strong></td>
      <td>${r.state_name}</td>
      <td><span class="scheme-badge ${schemeClass}">${schemeClass}</span></td>
      <td style="color: var(--text-secondary); font-size: 11px;">${r.ministry}</td>
      <td>${r.reason}</td>
    `;
    tbody.appendChild(tr);
  });
}
