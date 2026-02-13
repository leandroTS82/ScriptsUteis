(function () {
    const CONFIGS = [
    {
        day: "09",
        month: "02",
        year: "2026",
        period: "morning",
        description: `
Full validation of post-deploy flows: Theft Report creation, Zoho integration, Event Hub and Service Bus processing, status transitions, and correct email delivery with configured delay.
Document upload testing in DEV (via console), confirming proper behavior after adjustments.
Analysis of BE unavailability incident in DEV, including review of logs.
        `
    },
    {
        day: "09",
        month: "02",
        year: "2026",
        period: "afternoon",
        description: `
Work on ClickUp tickets, including clarification of status/step mapping and contacting Gijs for validation.
Creation of a detailed mapping spreadsheet (Zoho statuses × portal steps), including ordering, visibility, and adjustment points, shared with the team.
Continuous communication with Vini and Paulo during testing and environment stabilization.
        `
    }
];

    // =====================================================
    // ⚙️ CONFIGURAÇÃO FIXA
    // =====================================================
    const DEFAULTS = {
        customer: 74,
        project: 241,
        activity: 847
    };

    const PERIODS = {
        morning: { begin: "06:00", end: "12:00" },
        afternoon: { begin: "13:00", end: "15:00" }
    };

    // =====================================================
    // 🧠 ENGINE
    // =====================================================
    function buildBody(cfg) {
        const time = PERIODS[cfg.period];

        if (!time && (!cfg.begin || !cfg.end)) {
            throw new Error("❌ Período inválido ou horário manual incompleto.");
        }

        return {
            dtISO: `${cfg.year}-${cfg.month}-${cfg.day}`,
            dtBR: `${cfg.day}-${cfg.month}-${cfg.year}`,
            begin: cfg.begin || time.begin,
            end: cfg.end || time.end,
            customer: DEFAULTS.customer,
            project: DEFAULTS.project,
            activity: DEFAULTS.activity,
            description: cfg.description.trim()
        };
    }

    function calculateDuration(begin, end) {
        const [bh, bm] = begin.split(":").map(Number);
        const [eh, em] = end.split(":").map(Number);

        let start = bh * 60 + bm;
        let finish = eh * 60 + em;
        if (finish < start) finish += 24 * 60;

        const diff = finish - start;
        return `${String(Math.floor(diff / 60)).padStart(2, "0")}:${String(diff % 60).padStart(2, "0")}`;
    }

    // =====================================================
    // 🚀 EXECUTAR TIMESHEET EM SEQUÊNCIA
    // =====================================================
    function createTimesheet(body) {
        return new Promise((resolve, reject) => {
            $.ajax({
                url: `/pt_BR/timesheet/create?begin=${body.dtISO}`,
                method: "GET",
                headers: { "X-Requested-With": "XMLHttpRequest" },
                success: function (html) {
                    const temp = document.createElement("div");
                    temp.innerHTML = html;

                    const tokenInput = temp.querySelector('input[name*="_token"]');
                    if (!tokenInput) {
                        console.error("❌ CSRF token não encontrado.");
                        return reject();
                    }

                    const duration = calculateDuration(body.begin, body.end);

                    $.ajax({
                        url: "/pt_BR/timesheet/create",
                        method: "POST",
                        data: {
                            "timesheet_edit_form[begin]": `${body.dtBR} ${body.begin}`,
                            "timesheet_edit_form[end]": `${body.dtBR} ${body.end}`,
                            "timesheet_edit_form[duration]": duration,
                            "timesheet_edit_form[customer]": body.customer,
                            "timesheet_edit_form[project]": body.project,
                            "timesheet_edit_form[activity]": body.activity,
                            "timesheet_edit_form[description]": body.description,
                            "timesheet_edit_form[billableMode]": "auto",
                            "timesheet_edit_form[_token]": tokenInput.value
                        },
                        headers: { "X-Requested-With": "XMLHttpRequest" },
                        success: function () {
                            console.log(`✔ Timesheet criado | ${body.dtBR} ${body.begin}-${body.end}`);
                            resolve();
                        },
                        error: function (err) {
                            console.error("✖ Erro ao criar timesheet", err);
                            reject();
                        }
                    });
                },
                error: function (err) {
                    console.error("✖ Erro ao abrir modal (GET)", err);
                    reject();
                }
            });
        });
    }

    // =====================================================
    // ▶️ EXECUTA TODOS OS CONFIGS EM ORDEM
    // =====================================================
    async function runAll() {
        for (const cfg of CONFIGS) {
            const body = buildBody(cfg);
            await createTimesheet(body);
        }

        // Só recarrega após TODOS finalizarem
        console.log("✔ Todos os timesheets foram registrados.");
        setTimeout(() => location.reload(), 800);
    }

    runAll();

})();
