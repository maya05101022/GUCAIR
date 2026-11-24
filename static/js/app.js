/* GUCAIR interface behaviour */
(function () {
    "use strict";

    // Mobile dashboard sidebar
    const sidebar = document.getElementById("dashboardSidebar");
    const backdrop = document.querySelector(".sidebar-backdrop");
    const openers = document.querySelectorAll("[data-sidebar-open]");
    const closers = document.querySelectorAll("[data-sidebar-close]");

    function openSidebar() {
        if (!sidebar) return;
        sidebar.classList.add("is-open");
        if (backdrop) backdrop.classList.add("is-open");
        document.body.style.overflow = "hidden";
    }

    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove("is-open");
        if (backdrop) backdrop.classList.remove("is-open");
        document.body.style.overflow = "";
    }

    openers.forEach((el) => el.addEventListener("click", openSidebar));
    closers.forEach((el) => el.addEventListener("click", closeSidebar));

    // Confirmation prompts for destructive actions
    document.querySelectorAll("form[data-confirm]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (!window.confirm(form.dataset.confirm)) {
                event.preventDefault();
            }
        });
    });

    // Assessment completion progress
    const assessmentForm = document.querySelector("[data-assessment-form]");
    if (assessmentForm) {
        const questions = assessmentForm.querySelectorAll(".assess-question");
        const total = questions.length;
        const answeredCount = assessmentForm.querySelector("[data-answered-count]");
        const progressBar = assessmentForm.querySelector("[data-progress-bar]");
        const progressText = assessmentForm.querySelector("[data-progress-text]");

        function updateProgress() {
            let answered = 0;
            questions.forEach((question) => {
                if (question.querySelector('input[type="radio"]:checked')) answered += 1;
            });
            if (answeredCount) answeredCount.textContent = answered;
            if (progressBar) {
                const pct = total ? Math.round((answered / total) * 100) : 0;
                progressBar.style.width = pct + "%";
                progressBar.setAttribute("aria-valuenow", String(pct));
                if (progressText) progressText.textContent = pct + "%";
            }
        }
        assessmentForm.addEventListener("change", updateProgress);
        updateProgress();

        assessmentForm.addEventListener("submit", (event) => {
            let missing = false;
            questions.forEach((question) => {
                if (!question.querySelector('input[type="radio"]:checked')) missing = true;
            });
            if (missing) {
                event.preventDefault();
                const firstMissing = Array.from(questions).find(
                    (q) => !q.querySelector('input[type="radio"]:checked')
                );
                if (firstMissing) {
                    firstMissing.scrollIntoView({ behavior: "smooth", block: "center" });
                    const fieldLabel = firstMissing.querySelector(".q-label");
                    if (fieldLabel) fieldLabel.classList.add("text-danger");
                }
                const alertBox = document.getElementById("assessment-incomplete");
                if (alertBox) alertBox.classList.remove("d-none");
            }
        });
    }

    // Bootstrap tooltips
    if (window.bootstrap) {
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
            new window.bootstrap.Tooltip(el);
        });
    }
})();

/* Shared Chart.js theme helpers, used after Chart.js is loaded. */
window.GUCAIR = {
    palette: ["#0e2c52", "#1f9bb5", "#3d6f9e", "#b5852f", "#5f7f9e"],
    softPalette: ["#e8eff7", "#e4f5f8", "#eef2f8", "#faf3e4", "#eef3f8"],
    categoryColor(category) {
        return {
            Initial: "#b23b3b",
            Developing: "#b5852f",
            Advanced: "#3d6f9e",
            Leading: "#1f7a54"
        }[category] || "#3d6f9e";
    },
    baseOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        font: { family: "Inter, sans-serif", size: 11 },
                        usePointStyle: true,
                        boxWidth: 8,
                        padding: 14
                    }
                },
                tooltip: {
                    backgroundColor: "#0a2240",
                    titleFont: { family: "Inter, sans-serif", size: 12 },
                    bodyFont: { family: "Inter, sans-serif", size: 12 },
                    padding: 10,
                    cornerRadius: 7,
                    displayColors: true
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { family: "Inter, sans-serif", size: 10 }, color: "#6b7a8c" }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: "#eef2f7" },
                    ticks: { font: { family: "Inter, sans-serif", size: 10 }, color: "#6b7a8c" }
                }
            }
        };
    }
};
