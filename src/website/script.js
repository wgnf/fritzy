window.onload = function() {
    onWindowLoad();
}

function onWindowLoad() {
    handleThemeToggle();
}

function handleThemeToggle() {
    const themeToggle = document.querySelector('#theme-toggle');
    let currentTheme = localStorage.getItem('theme');

    if (!currentTheme) {
        currentTheme = 'light';
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
