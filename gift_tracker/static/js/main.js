document.addEventListener('DOMContentLoaded', function() {
    const giftCards = document.querySelectorAll('.gift-card');
    
    giftCards.forEach(card => {
        card.addEventListener('click', function() {
            this.classList.toggle('bg-blue-100');
        });
    });
});
