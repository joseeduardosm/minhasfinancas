/* Grafico mensal com Plotly para receitas e despesas. */

(function () {
    const dadosEl = document.getElementById("monthly-data");
    if (!dadosEl) {
        return;
    }

    const dados = JSON.parse(dadosEl.textContent);
    const labels = dados.labels;
    const receitas = dados.series.receitas;
    const despesas = dados.series.despesas;

    const eventosPorDia = {};
    Object.entries(dados.eventos_por_dia).forEach(([isoDate, lista]) => {
        const dia = Number(isoDate.split("-")[2]);
        eventosPorDia[dia] = lista.map((item) => item.label_tooltip).join("<br>");
    });

    const customData = labels.map((_, index) => {
        const dia = index + 1;
        return eventosPorDia[dia] || "Sem eventos no dia";
    });

    const traceReceitas = {
        x: labels,
        y: receitas,
        mode: "lines+markers",
        name: "Receitas",
        line: { color: "#1cb36a", width: 3 },
        marker: { color: "#1cb36a", size: 8 },
        customdata: customData,
        hovertemplate: "<b>Receitas</b><br>%{x}<br>%{customdata}<extra></extra>",
    };

    const traceDespesas = {
        x: labels,
        y: despesas,
        mode: "lines+markers",
        name: "Despesas",
        line: { color: "#de4a4a", width: 3 },
        marker: { color: "#de4a4a", size: 8 },
        customdata: customData,
        hovertemplate: "<b>Despesas</b><br>%{x}<br>%{customdata}<extra></extra>",
    };

    const layout = {
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(255,255,255,0.03)",
        font: { color: "#e8f0f8" },
        xaxis: {
            tickfont: { color: "#d2e1ee" },
            gridcolor: "rgba(255,255,255,0.08)",
        },
        yaxis: {
            tickprefix: "R$ ",
            tickfont: { color: "#d2e1ee" },
            gridcolor: "rgba(255,255,255,0.08)",
        },
        legend: { orientation: "h", y: 1.1 },
        margin: { l: 60, r: 30, t: 30, b: 50 },
        hoverlabel: { bgcolor: "#0f2438", bordercolor: "#467491" },
    };

    const config = {
        responsive: true,
        displayModeBar: true,
    };

    const chart = document.getElementById("finance-chart");
    Plotly.newPlot(chart, [traceDespesas, traceReceitas], layout, config);

    chart.on("plotly_click", function (eventData) {
        if (!eventData || !eventData.points || !eventData.points.length) {
            return;
        }

        const point = eventData.points[0];
        const day = point.pointNumber + 1;
        const target = `/welcome/calendario/?year=${dados.year}&month=${dados.month}&day=${day}`;
        window.location.href = target;
    });

})();
