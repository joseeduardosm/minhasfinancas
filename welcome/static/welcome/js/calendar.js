/* Calendario mensal com FullCalendar e tooltip por evento financeiro. */

(function () {
    const dadosEl = document.getElementById("monthly-data");
    const selectedDayEl = document.getElementById("selected-day");
    if (!dadosEl) {
        return;
    }

    const dados = JSON.parse(dadosEl.textContent);
    const selectedDay = selectedDayEl ? JSON.parse(selectedDayEl.textContent) : "";

    const eventos = dados.eventos.map((evento) => {
        const isReceita = evento.tipo === "RECEITA";
        return {
            id: String(evento.id),
            title: evento.nome,
            start: evento.data,
            allDay: true,
            backgroundColor: isReceita ? "#17a45f" : "#d74a4a",
            borderColor: isReceita ? "#17a45f" : "#d74a4a",
            extendedProps: {
                tooltip: evento.label_tooltip,
                status: evento.status,
                transacaoId: evento.id,
            },
        };
    });

    const tooltipEl = document.getElementById("event-tooltip");
    const actionsEl = document.getElementById("event-actions");
    const actionsTitleEl = document.getElementById("event-actions-title");
    const editLinkEl = document.getElementById("event-edit-link");
    const executeBtnEl = document.getElementById("event-execute-btn");
    const executeFormEl = document.getElementById("event-execute-form");
    const executeDayEl = document.getElementById("event-execute-day");

    function fecharAcoes() {
        if (!actionsEl) return;
        actionsEl.hidden = true;
    }

    const calendar = new FullCalendar.Calendar(document.getElementById("calendar"), {
        initialView: "dayGridMonth",
        locale: "pt-br",
        headerToolbar: false,
        initialDate: `${dados.year}-${String(dados.month).padStart(2, "0")}-01`,
        events: eventos,
        eventDidMount: function (info) {
            info.el.setAttribute("data-tooltip", info.event.extendedProps.tooltip || "");

            info.el.addEventListener("mouseenter", function () {
                const text = info.event.extendedProps.tooltip || "";
                if (!text) return;
                tooltipEl.textContent = text;
                tooltipEl.hidden = false;
            });

            info.el.addEventListener("mousemove", function (e) {
                tooltipEl.style.left = `${e.clientX + 12}px`;
                tooltipEl.style.top = `${e.clientY + 12}px`;
            });

            info.el.addEventListener("mouseleave", function () {
                tooltipEl.hidden = true;
            });
        },
        eventClick: function (info) {
            info.jsEvent.preventDefault();
            if (!actionsEl || !actionsTitleEl || !editLinkEl || !executeBtnEl || !executeFormEl) {
                return;
            }

            const transacaoId = info.event.extendedProps.transacaoId;
            if (!transacaoId) return;

            const selectedDayValue = selectedDay || String(info.event.start.getDate());
            const editUrl = `/welcome/lancamento/${transacaoId}/editar/?year=${dados.year}&month=${dados.month}&day=${selectedDayValue}`;

            actionsTitleEl.textContent = info.event.extendedProps.tooltip || info.event.title;
            editLinkEl.href = editUrl;
            executeBtnEl.disabled = info.event.extendedProps.status === "EXECUTADO";

            executeBtnEl.onclick = function () {
                if (executeBtnEl.disabled) return;
                if (executeDayEl) {
                    executeDayEl.value = selectedDayValue;
                }
                executeFormEl.action = `/welcome/lancamento/${transacaoId}/executar/`;
                executeFormEl.submit();
            };

            actionsEl.style.left = `${info.jsEvent.clientX + 12}px`;
            actionsEl.style.top = `${info.jsEvent.clientY + 12}px`;
            actionsEl.hidden = false;
        },
        dayCellDidMount: function (info) {
            if (!selectedDay) return;
            const day = Number(selectedDay);
            if (Number.isNaN(day)) return;
            if (info.date.getFullYear() !== dados.year) return;
            if (info.date.getMonth() + 1 !== dados.month) return;
            if (info.date.getDate() === day) {
                info.el.classList.add("day-selected");
            }
        },
    });

    calendar.render();

    document.addEventListener("click", function (event) {
        if (!actionsEl || actionsEl.hidden) return;
        if (actionsEl.contains(event.target)) return;
        if (event.target.closest(".fc-event")) return;
        fecharAcoes();
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            fecharAcoes();
            tooltipEl.hidden = true;
        }
    });
})();
