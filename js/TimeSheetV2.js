// ================================
// CONFIGURAÇÕES
// ================================
const CONFIGS = [
{
    day: "27",
    month: "02",
    year: "2026",
    period: "afternoon",
    description: `
Continuation of backend evolution for the Theft Report domain in the Allsetra Platform BE, including refinements in data modeling and adjustments to commands and handlers to support updated business rules.
Review and improvements in the integration flow responsible for synchronizing Theft Report information and related documents with Zoho CRM.
Additional structural adjustments and validations to ensure data consistency and preparation of the codebase for subsequent integration tests and feature continuation.
    `
}
];

// ================================
// REGRAS DE HORÁRIO
// ================================
const PERIOD_RULES = {
    morning: { start: "06:00", end: "12:00" },
    afternoon: { start: "13:00", end: "15:00" },
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