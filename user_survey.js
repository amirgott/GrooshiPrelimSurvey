const WORKER_URL = "https://grooshi-survey-proxy.amir-gottlieb.workers.dev";

function readTrafficSource() {
  const params = new URLSearchParams(window.location.search);
  const result = {};
  const utmSource = params.get("utm_source");
  const utmMedium = params.get("utm_medium");
  const utmCampaign = params.get("utm_campaign");
  const hasFbclid = params.has("fbclid");

  if (utmSource) result["_utm_source"] = utmSource;
  if (utmMedium) result["_utm_medium"] = utmMedium;
  if (utmCampaign) result["_utm_campaign"] = utmCampaign;

  if (utmSource) {
    result["_referrer_source"] = utmSource;
  } else if (hasFbclid) {
    result["_referrer_source"] = "facebook";
  } else if (document.referrer) {
    result["_referrer_source"] = new URL(document.referrer).hostname;
  } else {
    result["_referrer_source"] = "direct";
  }

  return result;
}

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

    Object.assign(payload, readTrafficSource());

    const submitBtn = document.getElementById("submitBtn");
    submitBtn.textContent = "שולח...";
    submitBtn.disabled = true;

    try {
      const response = await fetch(WORKER_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ survey_data: JSON.stringify(payload) }),
      });

      if (response.ok) {
        submitBtn.textContent = "נשלח בהצלחה!";
        submitBtn.classList.replace("bg-green-600", "bg-indigo-600");
      } else {
        submitBtn.textContent = "שגיאה - נסה שוב";
        submitBtn.classList.replace("bg-green-600", "bg-red-600");
        submitBtn.disabled = false;
      }
    } catch (err) {
      submitBtn.textContent = "שגיאה - נסה שוב";
      submitBtn.classList.replace("bg-green-600", "bg-red-600");
      submitBtn.disabled = false;
    }
  };
});
