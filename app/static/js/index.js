// ===== Chart =====
const rtChartEl = document.getElementById('rtChart');
const statChartEl = document.getElementById('statChart');

const makeTempDataset = (label, borderColor, backgroundColor) => ({
	label,
	data: [],
	borderWidth: 2,
	pointRadius: 2,
	tension: 0.3,
	borderColor,
	backgroundColor,
});

// ===== Stat chart X axis auto-scaling (IMPORTANT) =====
function pickTimeAxisConfig(fromMs, toMs) {
	const span = toMs - fromMs;
	const minute = 60_000;
	const hour = 60 * minute;
	const day = 24 * hour;

	// <= 6h: show minutes
	if (span <= 6 * hour) {
		return {
			unit: 'minute',
			maxTicksLimit: 10,
			displayFormats: { minute: 'HH:mm' },
			tooltipFormat: 'dd.MM.yyyy HH:mm:ss',
		};
	}

	// <= 2d: show hours (with midnight showing date)
	if (span <= 2 * day) {
		return {
			unit: 'hour',
			maxTicksLimit: 10,
			displayFormats: { hour: 'HH:mm' },
			tooltipFormat: 'dd.MM.yyyy HH:mm:ss',
		};
	}

	// <= 60d: show days as dd.MM (fixes "01 08 15" problem)
	if (span <= 60 * day) {
		return {
			unit: 'day',
			maxTicksLimit: 8,
			displayFormats: { day: 'dd.MM' },
			tooltipFormat: 'dd.MM.yyyy HH:mm:ss',
		};
	}

	// long ranges: months
	return {
		unit: 'month',
		maxTicksLimit: 8,
		displayFormats: { month: 'MM.yyyy' },
		tooltipFormat: 'dd.MM.yyyy HH:mm:ss',
	};
}

const rtChart = new Chart(rtChartEl, {
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
					duration: 600_000,
					delay: 100,
				},
			},
			y: {
				title: { display: true, text: '°C' },
			},
		},
	},
});

const statChart = new Chart(statChartEl, {
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
				type: 'time',
				time: {
					tooltipFormat: 'dd.MM.yyyy HH:mm',
				},
				ticks: {
					autoSkip: true,
					maxRotation: 0,
					maxTicksLimit: 8,
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

	refreshLastUpdate: (dateStr) => {
		const lastUpdateEl = document.getElementById('rt-last-update');
		if (!lastUpdateEl) return;
		lastUpdateEl.innerHTML = dateStr;
	},

	async reconnectLastDevice() {
		try {
			const json = await fetchJson('/current_bluetooth_connection');

			if (json?.success && json?.data) {
				this.clearDevicesList();
				this.addDevice(json.data, true);
				this.refreshLastUpdate(json.data?.last_update);

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

	async getLastMetrics(seconds) {
		try {
			const params = new URLSearchParams({ seconds });
			const json = await fetchJson(`/get_last_metrics?${params}`);
			if (json?.success) {
				json.data.forEach((item) => {
					let i = -1;
					if (item.name === 'Temp1') i = 0;
					if (item.name === 'Temp2') i = 1;

					if (i !== -1) {
						rtChart.data.datasets[i].data.push({ x: item.ts, y: item.value });
					}
				});
			} else {
				console.error(json);
			}
		} catch (err) {
			console.error(err);
		}
	},

	async getStatChartData(from, to) {
		try {
			const params = new URLSearchParams({
				from: getNowDateStr(from),
				to: getNowDateStr(to),
			});

			const json = await fetchJson(`/get_period_metrics?${params}`);
			if (json.success === undefined || !json.success) {
				console.error('get_period_metrics error');
				return;
			}

			if (statChart.data.datasets[0] !== undefined) {
				statChart.data.datasets[0].data = [];
			}

			if (statChart.data.datasets[1] !== undefined) {
				statChart.data.datasets[1].data = [];
			}

			json.data.forEach((item) => {
				let i = -1;
				if (item.name === 'Temp1') i = 0;
				if (item.name === 'Temp2') i = 1;

				if (i !== -1) {
					statChart.data.datasets[i].data.push({ x: item.ts, y: item.value });
				}
			});

			statChart.update('quiet');
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

	if (temps.t1 !== null) rtChart.data.datasets[0].data.push({ x: ts, y: temps.t1 });
	if (temps.t2 !== null) rtChart.data.datasets[1].data.push({ x: ts, y: temps.t2 });

	rtChart.update('quiet');
	bluetoothFunc.refreshLastUpdate(getNowDateStr(ts));
});

ws.addEventListener('error', (e) => {
	console.error('WebSocket error', e);
});

document.addEventListener('DOMContentLoaded', () => {
	if (!window.flatpickr) return;

	const input = document.getElementById('history-range');
	if (!input) return;

	const from = new Date().setHours(0, 0, 0, 0);
	const to = new Date().setHours(23, 59, 59, 999);

	flatpickr(input, {
		mode: 'range',
		enableTime: true,
		time_24hr: true,
		dateFormat: 'Y-m-d H:i:S',
		altInput: true,
		altFormat: 'd.m.Y H:i',
		defaultDate: [from, to],
		disableMobile: true,
		onChange: (selectedDates, dateStr, instance) => {
			let from = undefined;
			let to = undefined;

			if (selectedDates.length === 1) {
				from = new Date(selectedDates[0]).setHours(0, 0, 0, 0);
			}

			if (selectedDates.length === 2) {
				from = new Date(selectedDates[0]).setHours(0, 0, 0, 0);
				to = new Date(selectedDates[1]).setHours(23, 59, 59, 999);
			}

			if (from === undefined && to === undefined) return;

			let dates = [from];
			if (to !== undefined) {
				dates.push(to);
			}

			instance.setDate(dates, false);

			bluetoothFunc.getStatChartData(from, to);
		},
	});

	bluetoothFunc.getStatChartData(from, to);
});

bluetoothFunc.reconnectLastDevice();
bluetoothFunc.getLastMetrics(600);
