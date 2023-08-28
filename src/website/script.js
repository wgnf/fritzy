let currentTimespanSelection = '';

window.onload = function() {
    onWindowLoad();
}

function onWindowLoad() {
    handleThemeToggle();
    handleTimespanSelection();
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

function submitTimespanSelection() {
    console.log(`SUBMIT: ${currentTimespanSelection}`);
}
