/* Escolha de escopo para exclusao de eventos recorrentes. */

(function () {
    const forms = document.querySelectorAll(".delete-scope-form");
    if (!forms.length) {
        return;
    }

    function perguntarEscopo() {
        const escolha = window.prompt(
            "Excluir recorrencia:\n1 = apenas este evento\n2 = deste evento em diante\n3 = todos os relacionados\n\nDigite 1, 2 ou 3:",
            "3"
        );

        if (escolha === null) {
            return null;
        }

        const opcao = String(escolha).trim();
        if (opcao === "1") return "one";
        if (opcao === "2") return "from";
        if (opcao === "3") return "all";
        return "";
    }

    forms.forEach((form) => {
        form.addEventListener("submit", function (event) {
            const recurringInput = form.querySelector('input[name="is_recurring"]');
            const scopeInput = form.querySelector('input[name="delete_scope"]');
            const isRecurring = recurringInput && recurringInput.value === "1";

            if (!scopeInput) {
                return;
            }

            if (!isRecurring) {
                scopeInput.value = "all";
                return;
            }

            const scope = perguntarEscopo();
            if (!scope) {
                event.preventDefault();
                return;
            }
            scopeInput.value = scope;
        });
    });
})();
