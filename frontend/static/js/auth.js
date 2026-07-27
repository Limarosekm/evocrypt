let authMode = "signin";

// Switch between Login and Register
function setAuthMode(mode) {
    authMode = mode;

    const title = document.getElementById("form-title");
    const submitBtn = document.getElementById("submit-btn");
    const toggle = document.getElementById("auth-toggle-text");
    const emailLabel = document.querySelector("label[for='email']");

    clearError();

    if (mode === "signup") {
        title.textContent = "Create your Account";
        submitBtn.textContent = "Register";
        emailLabel.textContent = "Email";
        toggle.innerHTML =
            'Already have an account? <a href="#" onclick="setAuthMode(\'signin\');return false;">Sign In</a>';
    } else {
        title.textContent = "Sign in to EvoCrypt";
        submitBtn.textContent = "Sign In";
        emailLabel.textContent = "Username";
        toggle.innerHTML =
            'New here? <a href="#" onclick="setAuthMode(\'signup\');return false;">Create an account</a>';
    }
}

function showError(message) {
    const error = document.getElementById("auth-error");
    error.style.display = "block";
    error.textContent = message;
}

function clearError() {
    const error = document.getElementById("auth-error");
    error.style.display = "none";
    error.textContent = "";
}

function setLoading(status) {
    const btn = document.getElementById("submit-btn");
    btn.disabled = status;

    if (status) {
        btn.textContent = "Please wait...";
    } else {
        btn.textContent = authMode === "signup" ? "Register" : "Sign In";
    }
}

async function handleAuthSubmit(event) {
    event.preventDefault();

    clearError();
    setLoading(true);

    const emailOrUsername = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    try {

        let endpoint;
        let payload;

        if (authMode === "signup") {

            endpoint = "/api/register";

            payload = {
                username: emailOrUsername,
                email: emailOrUsername,
                password: password
            };

        } else {

            endpoint = "/api/login";

            payload = {
                username: emailOrUsername,
                password: password
            };

        }

        const response = await fetch(endpoint, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(payload)

        });

        const result = await response.json();

        if (result.success) {

            if (authMode === "signup") {

                alert("Registration Successful!");

                document.getElementById("password").value = "";

                setAuthMode("signin");

            } else {

                window.location.href = "/dashboard";

            }

        } else {

            showError(result.message);

        }

    } catch (err) {

        console.error(err);

        showError("Unable to connect to server.");

    }

    setLoading(false);
}