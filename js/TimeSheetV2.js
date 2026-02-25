// ================================
// CONFIGURAÇÕES
// ================================
const CONFIGS = [
    {
        day: "16",
        month: "02",
        year: "2026",
        period: "morning",
        description: `
Full validation of post-deploy flows: Theft Report creation, Zoho integration, Event Hub and Service Bus processing, status transitions, and correct email delivery with configured delay.
Document upload testing in DEV (via console), confirming proper behavior after adjustments.
Analysis of BE unavailability incident in DEV, including review of logs.
        `
    }
];

// ================================
// REGRAS DE HORÁRIO
// ================================
const PERIOD_RULES = {
    morning: { start: "09:00", end: "12:00" },
    afternoon: { start: "13:00", end: "18:00" },
    full: { start: "09:00", end: "18:00" }
};

// ================================
// FUNÇÃO PRINCIPAL
// ================================
function applyConfigs() {
    CONFIGS.forEach(cfg => {
        const rule = PERIOD_RULES[cfg.period];
        if (!rule) {
            console.warn("Período inválido:", cfg.period);
            return;
        }

        const formattedBegin = `${cfg.day}-${cfg.month}-${cfg.year} ${rule.start}`;
        const formattedEnd = `${cfg.day}-${cfg.month}-${cfg.year} ${rule.end}`;

        const beginField = document.getElementById("timesheet_edit_form_begin");
        const endField = document.getElementById("timesheet_edit_form_end");
        const descField = document.getElementById("timesheet_edit_form_description");

        if (!beginField || !endField || !descField) {
            console.error("Campos do formulário não encontrados.");
            return;
        }

        // Atualiza campos
        beginField.value = formattedBegin;
        endField.value = formattedEnd;
        descField.value = cfg.description.trim();

        // Dispara eventos para recalcular duração
        if (window.jQuery) {
            jQuery(beginField).change();
            jQuery(endField).change();
        }

        console.log(`✔ Formulário atualizado para ${formattedBegin}`);
    });
}

// ================================
// EXECUÇÃO AUTOMÁTICA
// ================================
applyConfigs();