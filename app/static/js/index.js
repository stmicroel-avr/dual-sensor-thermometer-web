const myChart = new Chart(document.getElementById('myChart'), {
    type: 'line',
    data: {
        datasets: [
            {
                label: 'Temp1',
                data: [],
                borderWidth: 2,
                pointRadius: 2,
                tension: 0.3,
                borderColor: '#36A2EB',
                backgroundColor: 'rgba(54,162,235,0.15)',
            },
            {
                label: 'Temp2',
                data: [],
                borderWidth: 2,
                pointRadius: 2,
                tension: 0.3,
                borderColor: '#FF6384',
                backgroundColor: 'rgba(255,99,132,0.15)',
            }
        ]
    },
    options: {
        animation: false,
        parsing: false,

        scales: {
            x: {
                type: 'realtime',
                realtime: {
                    duration: 300_000,
                    delay: 500
                }
            },
            y: {
                title: {display: true, text: '°C'}
            }
        }
    }
});

const bluetoothFunc = {
    updateTitle: (devices) =>
        document.getElementById('devices-title').innerHTML = 'Devices (found ' + devices.length + ')',
    toggleLoader: (spin) => {
        const el = document.getElementById('scan-loader');
        if (spin) {
            el.classList.add('spin');
            el.parentNode.setAttribute('disabled', 'disabled');
            document.getElementById('devices-list').innerHTML = '<h6 class="text-secondary">Scanning...</h6>';
        } else {
            el.classList.remove('spin');
            el.parentNode.removeAttribute('disabled');
            document.getElementById('devices-list').innerHTML = '';
        }
    },
    scan: () => {
        bluetoothFunc.toggleLoader(true);
        (async () => {
            const response = await fetch("/scan");
            const devices = await response.json();
            bluetoothFunc.toggleLoader(false);
            if (devices.data !== undefined) {
                bluetoothFunc.updateTitle(devices.data);
                for (const device of devices.data) {
                    bluetoothFunc.add_device(device);
                }
            }
        })();
    },
    connect: (addr) => {
        (async () => {
            const response = await fetch("/connect", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({'addr': addr}),
            });
            const data = await response.json();
            console.log(data);
        })();
    },
    add_device: (device) => {
        const container = document.getElementById('devices-list');

        const linkEl = document.createElement('a');
        linkEl.addEventListener('click', (e) => {
            const els = document.getElementsByClassName('list-group-item');
            for (let i = 0; i < els.length; i++) {
                els[i].classList.remove('active');
            }
            e.currentTarget.classList.add('active');
            bluetoothFunc.connect(device.addr);
        });

        linkEl.classList.add('list-group-item', 'list-group-item-action', 'flex-column', 'cursor-pointer')
        const divEl = document.createElement('div');
        divEl.classList.add('d-flex', 'w-100', 'justify-content-between');
        const nameEl = document.createElement('h6');
        nameEl.classList.add('mb-1');
        const dateEl = document.createElement('small');
        const addrEl = document.createElement('small');

        dateEl.append(device.time);
        nameEl.append(device.name);
        addrEl.append(device.addr);

        divEl.append(nameEl, dateEl);
        linkEl.append(divEl, addrEl);
        container.append(linkEl);
    },
}

bluetoothFunc.scan();

(new WebSocket("/ws"))
    .addEventListener('message', (e) => {
        const data = JSON.parse(e.data);
        const ts = Date.now();
        console.log({
            ts: ts,
            t1: data.Temp1,
            t2: data.Temp2,
        })

        myChart.data.datasets[0].data.push({x: ts, y: data.Temp1});
        myChart.data.datasets[1].data.push({x: ts, y: data.Temp2});
        myChart.update('quiet');
    });
