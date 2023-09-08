let currentTimespanSelection = '';
let chart = undefined;

const apiEndpoint = 'http://localhost:8081';

window.onload = function() {
    onWindowLoad();
}

function onWindowLoad() {
    handleThemeToggle();
    handleTimespanSelection();
    createChart();
    submitTimespanSelection(); // fire once to show data
    handleTotals();
}

function handleThemeToggle() {
    const themeToggle = document.querySelector('#theme-toggle');
    let currentTheme = localStorage.getItem('theme');

    if (!currentTheme) {
        currentTheme = 'dark';
    }

    document.documentElement.setAttribute('theme', currentTheme);
    if (currentTheme == 'dark') {
        themeToggle.checked = true;
    }

    themeToggle.addEventListener('change', () => {
        let theme = '';

        if (themeToggle.checked) {
            theme = 'dark';
        } else {
            theme = 'light';
        }

        document.documentElement.setAttribute('theme', theme);
        localStorage.setItem('theme', theme);
    });
}

function handleTimespanSelection() {
    const customTimespanInput = document.querySelector('#timespan-select-number-days');
    const timespanSelectRadios = document.timespanSelect.timespanSelectRadios;
    currentTimespanSelection = timespanSelectRadios.value;

    changeHandler = () => {
        if (timespanSelectRadios.value !== currentTimespanSelection) {
            currentTimespanSelection = timespanSelectRadios.value;
        }

        customTimespanInput.style.display = currentTimespanSelection === 'custom'
            ? 'block'
            : 'none';
    }
    
    timespanSelectRadios.forEach(element => {
        element.addEventListener('change', changeHandler);
    });

    // execute 'changeHandler' once, so that UI is updated with current value
    changeHandler();
}

function createChart() {
    const chartCanvas = document.querySelector('#chart-container > canvas');

    chart = new Chart(chartCanvas, {
        type: 'bar',
        options: {
            plugins: {
                title: {
                    display: false,
                },
                legend: {
                    labels: {
                        font: {
                            family: 'Quicksand',
                        },
                    },
                },
            },
            responsive: true,
            scales: {
                x: {
                    stacked: true,
                },
                y: {
                    stacked: true,
                },
            },
        },
    });
}

function handleTotals() {
    fetch(`${apiEndpoint}/total`)
        .then(response => {
            if (!response.ok) {
                throw new Error(response.error);
            }

            return response.json();
        })
        .then(json => showTotals(json))
        .catch(error => console.error(`Getting internet statics failed: ${error.message}`));
}

function showTotals(totalsJson) {
    const totalDisplay = document.querySelector('#total-total');
    totalDisplay.textContent = formatMegabytes(totalsJson.total_megabytes);

    const totalSentDisplay = document.querySelector('#total-sent');
    totalSentDisplay.textContent = formatMegabytes(totalsJson.total_megabytes_sent);

    const totalReceivedDisplay = document.querySelector('#total-received');
    totalReceivedDisplay.textContent = formatMegabytes(totalsJson.total_megabytes_received);

    const totalConnectionsDisplay = document.querySelector('#total-connections');
    totalConnectionsDisplay.textContent = totalsJson.total_connections;

    const totalOnlineTimeDisplay = document.querySelector('#total-online');
    totalOnlineTimeDisplay.textContent = totalsJson.total_online_time;

    const totalSinceDisplay = document.querySelector('#total-since');
    const formattedTotalSince = formatDate(totalsJson.since_date);

    totalSinceDisplay.textContent = formattedTotalSince;
}

function submitTimespanSelection() {
    let days = undefined;
    switch (currentTimespanSelection) {
        case('all'):
            days = undefined;
            break;
        case('month'):
            days = 30;
            break;
        case('custom'):
            const customTimespanInput = document.querySelector('#timespan-select-number-days');
            days = parseInt(customTimespanInput.value);
            break;
    }

    let url = `${apiEndpoint}/items`;
    if (days) {
        url = `${url}?days=${days}`;
    }

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(response.error);
            }

            return response.json();
        })
        .then(json => updateChart(json))
        .catch(error => console.error(`Getting internet statics failed: ${error.message}`));
}

function updateChart(dataJson) {
    const labels = dataJson.map(item => {
        return formatDate(item.date);
    });

    const sent = dataJson.map(item => {
        return item.megabytes_sent;
    });

    const received = dataJson.map(item => {
        return item.megabytes_received;
    });
    
    const datasets = [
        {
            label: 'sent (MB)',
            data: sent,
        },
        {
            label: 'received (MB)',
            data: received,
        },
    ];

    chart.data = {
        labels: labels,
        datasets: datasets,
    };

    chart.update();
}

function formatMegabytes(megabytes) {
    if (megabytes <= 1024) {
        return `${megabytes.toFixed(2)} MB`;
    }

    return `${(megabytes / 1024).toFixed(2)} GB`;
}

function formatDate(isoDate) {
    const date = new Date(isoDate);

    const options = { year: 'numeric', month: '2-digit', day: '2-digit' };
    const formatted = date.toLocaleDateString('de-DE', options);

    return formatted;
}
