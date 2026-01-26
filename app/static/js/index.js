const ctx = document.getElementById('myChart');

new Chart(ctx, {
    type: 'bar',
    data: {
        labels: ['Red', 'Blue', 'Yellow', 'Green', 'Purple', 'Orange'],
        datasets: [{
            label: '# of Votes',
            data: [12, 19, 3, 5, 2, 3],
            borderWidth: 1
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true
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
    .addEventListener('message', (e) => console.log(e));