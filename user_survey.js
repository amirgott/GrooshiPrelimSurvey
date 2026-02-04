const WORKER_URL = "https://grooshi-survey-proxy.amir-gottlieb.workers.dev";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("masterForm");

  window.submitSurvey = async function () {
    const data = new FormData(form);
    const payload = {};

    // Handle checkboxes with same name (aggregate into arrays)
    for (const [key, value] of data.entries()) {
      if (value === "") continue;
      if (payload[key]) {
        payload[key] = payload[key] + ", " + value;
      } else {
        payload[key] = value;
      }
    }

    const submitBtn = document.querySelector("#stepFinal button");
    const originalText = submitBtn.textContent;
    submitBtn.textContent = "שולח...";
    submitBtn.disabled = true;

    try {
      const response = await fetch(WORKER_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        submitBtn.textContent = "נשלח בהצלחה!";
        submitBtn.classList.replace("bg-indigo-600", "bg-green-600");
      } else {
        submitBtn.textContent = "שגיאה - נסה שוב";
        submitBtn.classList.replace("bg-indigo-600", "bg-red-600");
        submitBtn.disabled = false;
      }
    } catch (err) {
      submitBtn.textContent = "שגיאה - נסה שוב";
      submitBtn.classList.replace("bg-indigo-600", "bg-red-600");
      submitBtn.disabled = false;
    }
  };
});
