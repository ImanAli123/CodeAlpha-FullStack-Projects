
document.addEventListener("DOMContentLoaded", () => {
    // Automatically hide success and info messages.
    document.querySelectorAll(".message").forEach((message) => {
        window.setTimeout(() => {
            message.style.transition = "opacity 0.4s";
            message.style.opacity = "0";
            window.setTimeout(() => message.remove(), 450);
        }, 3500);
    });

    // Prevent accidental double submission of forms.
    document.querySelectorAll("form").forEach((form) => {
        form.addEventListener("submit", () => {
            if (form.checkValidity()) {
                const button = form.querySelector(
                    'button[type="submit"]'
                );
                if (button && !form.dataset.confirmed) {
                    button.style.opacity = "0.8";
                }
            }
        });
    });
});
