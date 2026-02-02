// ===== Chart =====
const chartEl = document.getElementById('myChart');
const makeTempDataset = (label, borderColor, backgroundColor) => ({
  label,
  data: [],
  borderWidth: 2,
  pointRadius: 2,
  tension: 0.3,
  borderColor,
  backgroundColor,
});

const myChart = new Chart(chartEl, {
  type: 'line',
  data: {
    datasets: [
      makeTempDataset('OnBoard', '#36A2EB', 'rgba(54,162,235,0.15)'),
      makeTempDataset('OnWire', '#FF6384', 'rgba(255,99,132,0.15)'),
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    parsing: false,
    scales: {
      x: {
        type: 'realtime',
        realtime: {
          duration: 300_000,
          delay: 100,
        },
      },
      y: {
        title: { display: true, text: '°C' },
      },
    },
  },
});

// ===== Small DOM helpers =====
const $ = (id) => document.getElementById(id);

const devicesTitleEl = $('devices-title');
const devicesListEl = $('devices-list');
const scanLoaderEl = $('scan-loader'); // icon inside button (as in your code)
const scanBtnEl = scanLoaderEl?.parentNode; // button

const setHtml = (el, html) => {
  if (!el) return;
  el.innerHTML = html;
};

const setDisabled = (el, disabled) => {
  if (!el) return;
  if (disabled) el.setAttribute('disabled', 'disabled');
  else el.removeAttribute('disabled');
};

const safeText = (v) => (v ?? '').toString();

// ===== Network helper =====
async function fetchJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    // Give a useful error message; caller can toast it.
    const text = await res.text().catch(() => '');
    throw new Error(`HTTP ${res.status} on ${url}${text ? `: ${text}` : ''}`);
  }
  return res.json();
}

// ===== Bluetooth UI/logic =====
const bluetoothFunc = {
  updateTitle(devices) {
    if (!devicesTitleEl) return;
    const count = Array.isArray(devices) ? devices.length : 0;
    devicesTitleEl.textContent = `Devices (found ${count})`;
  },

  toggleLoader(spin) {
    if (!scanLoaderEl) return;

    scanLoaderEl.classList.toggle('spin', !!spin);
    setDisabled(scanBtnEl, !!spin);

    // Keep behavior same, but avoid re-querying DOM
    setHtml(devicesListEl, spin ? '<h6 class="text-secondary">Scanning...</h6>' : '');
  },

  clearDevicesList() {
    setHtml(devicesListEl, '');
  },

  setActiveDeviceLink(clickedLinkEl) {
    // Less work than looping through all list-group-item on every click:
    // remove only the previous active one, then set new.
    const active = devicesListEl?.querySelector('.list-group-item.active');
    if (active) active.classList.remove('active');
    if (clickedLinkEl) clickedLinkEl.classList.add('active');
  },

  async scan() {
    try {
      this.toggleLoader(true);
      this.clearDevicesList();

      const devices = await fetchJson('/scan');
      this.toggleLoader(false);

      if (Array.isArray(devices?.data)) {
        this.updateTitle(devices.data);
        devices.data.forEach((device) => this.addDevice(device, false));
      } else {
        this.updateTitle([]);
      }
    } catch (err) {
      this.toggleLoader(false);
      console.error(err);

      // Optional: show a toast if Toastify exists
      if (window.Toastify) {
        Toastify({
          close: true,
          duration: 5000,
          gravity: 'bottom',
          position: 'right',
          text: `Scan failed: ${err.message}`,
        }).showToast();
      }
    }
  },

  async connect(addr, name, time) {
    try {
      const data = await fetchJson('/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ addr, name, time }),
      });

      console.log(data?.success);

      if (!data?.success && window.Toastify) {
        Toastify({
          close: true,
          duration: 5000,
          gravity: 'bottom',
          position: 'right',
          text: `Connect failed${data?.error ? `: ${data.error}` : ''}`,
        }).showToast();
      }
    } catch (err) {
      console.error(err);
      if (window.Toastify) {
        Toastify({
          close: true,
          duration: 5000,
          gravity: 'bottom',
          position: 'right',
          text: `Connect failed: ${err.message}`,
        }).showToast();
      }
    }
  },

  addDevice(device, isActive = false) {
    if (!devicesListEl) return;

    const linkEl = document.createElement('a');
    linkEl.href = '#'; // make it "link-like" but prevent navigation
    linkEl.classList.add(
      'list-group-item',
      'list-group-item-action',
      'flex-column',
      'cursor-pointer'
    );
    if (isActive) linkEl.classList.add('active');

    // Layout
    const headerEl = document.createElement('div');
    headerEl.classList.add('d-flex', 'w-100', 'justify-content-between');

    const nameEl = document.createElement('h6');
    nameEl.classList.add('mb-1');
    nameEl.textContent = safeText(device?.name) || '(unnamed)';

    const dateEl = document.createElement('small');
    dateEl.textContent = safeText(device?.time);

    const addrEl = document.createElement('small');
    addrEl.textContent = safeText(device?.addr);

    headerEl.append(nameEl, dateEl);
    linkEl.append(headerEl, addrEl);

    // Click
    linkEl.addEventListener('click', (e) => {
      e.preventDefault(); // avoid jumping to top due to "#"
      this.setActiveDeviceLink(linkEl);
      this.connect(device?.addr, device?.name, device?.time);
    });

    devicesListEl.append(linkEl);
  },

  async reconnectLastDevice() {
    try {
      const json = await fetchJson('/current_bluetooth_connection');

      if (json?.success && json?.data) {
        this.clearDevicesList();
        this.addDevice(json.data, true);

        if (window.Toastify) {
          Toastify({
            close: true,
            duration: 5000,
            newWindow: true,
            gravity: 'bottom',
            position: 'right',
            stopOnFocus: true,
            style: { background: 'linear-gradient(to right, #00b09b, #96c93d)' },
            text: `Already connected to device ${safeText(json.data.name)}`,
          }).showToast();
        }
      }
    } catch (err) {
      console.error(err);
    }
  },
};

// ===== WebSocket -> chart =====
function parseWsPayload(raw) {
  // Your backend sends something like: {"Temp1":"25.93","Temp2":"24.00"} (strings are common)
  const obj = JSON.parse(raw);
  const t1 = Number(obj?.Temp1);
  const t2 = Number(obj?.Temp2);

  // Don't push NaN to chart
  return {
    t1: Number.isFinite(t1) ? t1 : null,
    t2: Number.isFinite(t2) ? t2 : null,
  };
}

const ws = new WebSocket('/ws');

ws.addEventListener('message', (e) => {
  let temps;
  try {
    temps = parseWsPayload(e.data);
  } catch (err) {
    console.warn('Bad WS payload:', e.data);
    return;
  }

  const ts = Date.now();

  // Optional debug
  // console.log({ ts, t1: temps.t1, t2: temps.t2 });

  if (temps.t1 !== null) myChart.data.datasets[0].data.push({ x: ts, y: temps.t1 });
  if (temps.t2 !== null) myChart.data.datasets[1].data.push({ x: ts, y: temps.t2 });

  myChart.update('quiet');
});

ws.addEventListener('error', (e) => {
  console.error('WebSocket error', e);
});

bluetoothFunc.reconnectLastDevice();

// If you call scan from HTML onclick, keep it accessible
// window.bluetoothFunc = bluetoothFunc;
