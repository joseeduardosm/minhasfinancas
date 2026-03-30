/* Exibe campos de recorrencia somente quando usuario ativa a opcao. */

(function () {
    const checkbox = document.getElementById("is_recorrente");
    const container = document.querySelector(".recorrencia-fields");
    if (!checkbox || !container) {
        return;
    }

    const fields = container.querySelectorAll("[data-recorrencia-field]");

    function sync() {
        const enabled = checkbox.checked;
        container.hidden = !enabled;
        fields.forEach((field) => {
            field.required = enabled;
        });
    }

    checkbox.addEventListener("change", sync);
    sync();
})();
