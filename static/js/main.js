document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const icon = themeToggle.querySelector('i');

    function setTheme(theme) {
        body.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);
        icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }

    themeToggle.addEventListener('click', function() {
        const currentTheme = body.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    });

    // Check for saved theme preference or use dark as default
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);

    const giftCards = document.querySelectorAll('.gift-card');
    giftCards.forEach(card => {
        card.addEventListener('click', function() {
            this.classList.toggle('bg-light');
        });
    });
});
