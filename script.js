const API_BASE_URL = window.CHURN_API_BASE_URL || "http://127.0.0.1:8000";

const churnForm = document.getElementById("churnForm");
const predictBtn = document.getElementById("predictBtn");
const resultBox = document.getElementById("result");
const errorMessage = document.getElementById("errorMessage");

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove("hidden");
}

function hideError() {
    errorMessage.textContent = "";
    errorMessage.classList.add("hidden");
}

function renderPrediction(result) {
    const isHighRisk = result.churn_prediction === 1;
    const label = isHighRisk ? "High Churn Risk" : "Low Churn Risk";
    const info = isHighRisk
        ? "Retention outreach recommended for this customer."
        : "This customer appears stable based on current profile.";

    resultBox.classList.remove("hidden", "result-low", "result-high");
    resultBox.classList.add(isHighRisk ? "result-high" : "result-low");
    resultBox.innerHTML = `
        <div>
            <h3>${label}</h3>
            <p>${info}</p>
        </div>
        <strong>${result.churn_probability}%</strong>
    `;
}

function resetResult() {
    resultBox.classList.add("hidden");
    resultBox.classList.remove("result-low", "result-high");
    resultBox.innerHTML = "";
}

churnForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideError();
    resetResult();

    if (!churnForm.checkValidity()) {
        showError("Please fill all required fields with valid values.");
        churnForm.reportValidity();
        return;
    }

    const formData = new FormData(churnForm);
    const payload = Object.fromEntries(formData.entries());

    payload.tenure = Number.parseInt(payload.tenure, 10);
    payload.MonthlyCharges = Number.parseFloat(payload.MonthlyCharges);
    payload.TotalCharges = Number.parseFloat(payload.TotalCharges);
    payload.SeniorCitizen = Number.parseInt(payload.SeniorCitizen, 10);

    predictBtn.disabled = true;
    predictBtn.textContent = "Scoring...";

    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (!response.ok) {
            const detail = result.detail || "Prediction failed. Please verify backend server and input.";
            showError(detail);
            return;
        }

        renderPrediction(result);
    } catch (error) {
        showError(
            "Unable to reach backend API. Start FastAPI server at " +
            `${API_BASE_URL} and retry.`
        );
    } finally {
        predictBtn.disabled = false;
        predictBtn.textContent = "Predict Churn Risk";
    }
});
