(function () {
    const CONFIGS = [
        {
            day: "06",
            month: "02",
            year: "2026",
            period: "morning",
            description: `
Consolidation of multiple PRs into a single stable PR (#41) after the automated review failed.
Included the delay feature for notification sending, as requested.
Performed the definitive removal of HasData for FAQ, StepDefinition, and StepDefinitionTranslation, replacing them with SQL insert scripts for data loading.
            `
        },
        {
            day: "06",
            month: "02",
            year: "2026",
            period: "afternoon",
            description: `
Inserted SQL scripts into the database to support the DEV environment.
Validated the migration and reviewed Azure Blob Storage configuration for document upload.
Identified instability in the DEV environment after deployment; alignment made to resume the analysis on Monday, respecting the team's resting period.
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
