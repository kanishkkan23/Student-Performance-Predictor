
const API_URL = "http://127.0.0.1:8000";

const loginSection = document.getElementById("loginSection");
const appSection = document.getElementById("appSection");
const loginError = document.getElementById("loginError");

const result = document.getElementById("result");
const error = document.getElementById("error");

const historyBody = document.getElementById("historyBody");
const predictButton = document.getElementById("predictButton");


// GOOGLE LOGIN CALLBACK

window.handleGoogleCredential = async function (response) {

    loginError.textContent = "Signing in...";

    try {

        const apiResponse = await fetch(`${API_URL}/auth/google`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                credential: response.credential
            })
        });

        const data = await apiResponse.json();

        if (!apiResponse.ok) {
            throw new Error(data.detail || "Google login failed");
        }

        // Store our application's JWT for this browser tab
        sessionStorage.setItem("access_token", data.access_token);

        loginError.textContent = "";

        showApplication(data.user);

    } catch (err) {

        loginError.textContent = err.message;

    }

};


// SHOW APPLICATION AFTER LOGIN

function showApplication(user) {

    loginSection.hidden = true;
    appSection.hidden = false;

    document.getElementById("userName").textContent = user.name;
    document.getElementById("userEmail").textContent = user.email;

    const picture = document.getElementById("userPicture");

    if (user.picture) {
        picture.src = user.picture;
        picture.hidden = false;
    } else {
        picture.hidden = true;
    }

    loadHistory();

}


// AUTHENTICATION HEADER

function getAuthHeaders() {

    const token = sessionStorage.getItem("access_token");

    return {
        "Authorization": `Bearer ${token}`
    };

}


// RESTORE EXISTING LOGIN SESSION

async function restoreSession() {

    const token = sessionStorage.getItem("access_token");

    if (!token) {
        return;
    }

    try {

        const response = await fetch(`${API_URL}/me`, {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error("Session expired");
        }

        const user = await response.json();

        showApplication(user);

    } catch (err) {

        sessionStorage.removeItem("access_token");

    }

}


// STUDENT PERFORMANCE PREDICTION

document.getElementById("predictionForm").addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();

        result.textContent = "";
        error.textContent = "";
        predictButton.disabled = true;

        const studentData = {
            study_hours: Number(document.getElementById("study_hours").value),
            attendance: Number(document.getElementById("attendance").value),
            previous_score: Number(document.getElementById("previous_score").value),
            assignment_score: Number(document.getElementById("assignment_score").value)
        };

        try {

            const response = await fetch(`${API_URL}/predict`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...getAuthHeaders()
                },
                body: JSON.stringify(studentData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Prediction failed");
            }

            result.textContent =
                `Predicted Score: ${data.predicted_score} | Performance: ${data.performance}`;

            await loadHistory();

        } catch (err) {

            error.textContent = err.message;

        } finally {

            predictButton.disabled = false;

        }

    }
);


// LOAD PERSONAL PREDICTION HISTORY

async function loadHistory() {

    try {

        const response = await fetch(`${API_URL}/history`, {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error("Unable to load prediction history");
        }

        const records = await response.json();

        historyBody.replaceChildren();

        if (records.length === 0) {

            const row = historyBody.insertRow();
            const cell = row.insertCell();

            cell.colSpan = 8;
            cell.textContent = "No prediction history available";

            return;
        }

        records.forEach(function (record) {

            const row = historyBody.insertRow();

            const values = [
                record.id,
                record.study_hours,
                record.attendance,
                record.previous_score,
                record.assignment_score,
                record.predicted_score,
                record.performance,
                record.created_at
            ];

            values.forEach(function (value) {

                const cell = row.insertCell();
                cell.textContent = value;

            });

        });

    } catch (err) {

        historyBody.replaceChildren();

        const row = historyBody.insertRow();
        const cell = row.insertCell();

        cell.colSpan = 8;
        cell.textContent = err.message;

    }

}


// REFRESH HISTORY BUTTON

document.getElementById("historyButton").addEventListener(
    "click",
    loadHistory
);


// SIGN OUT

document.getElementById("logoutButton").addEventListener(
    "click",
    function () {

        sessionStorage.removeItem("access_token");

        if (window.google && window.google.accounts) {
            window.google.accounts.id.disableAutoSelect();
        }

        appSection.hidden = true;
        loginSection.hidden = false;

        document.getElementById("predictionForm").reset();

        result.textContent = "";
        error.textContent = "";
        loginError.textContent = "";

        historyBody.replaceChildren();

    }
);


// CHECK LOGIN WHEN PAGE OPENS

restoreSession();
