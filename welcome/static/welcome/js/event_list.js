/* Comportamento do modal de criacao de lancamento na listagem mensal. */

(function () {
    const openBtn = document.getElementById("open-create-modal");
    const closeBtn = document.getElementById("close-create-modal");
    const modal = document.getElementById("create-modal");

    if (!openBtn || !closeBtn || !modal) {
        return;
    }

    function openModal() {
        modal.hidden = false;
    }

    function closeModal() {
        modal.hidden = true;
    }

    openBtn.addEventListener("click", openModal);
    closeBtn.addEventListener("click", closeModal);

    modal.addEventListener("click", function (event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeModal();
        }
    });
})();
