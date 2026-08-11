let authMode = "signin";


function setAuthMode(mode) {

    authMode = mode;

    clearError();


    const title =
        document.getElementById("form-title");

    const submitButton =
        document.getElementById("submit-btn");

    const emailLabel =
        document.querySelector(
            "label[for='email']"
        );

    const toggle =
        document.getElementById(
            "auth-toggle-text"
        );


    if (mode === "signup") {

        title.textContent =
            "Create your Account";

        submitButton.textContent =
            "Register";

        emailLabel.textContent =
            "Email / Username";

        toggle.innerHTML =
            'Already have an account? ' +
            '<a href="#" ' +
            'onclick="setAuthMode(\'signin\'); return false;">' +
            'Sign In</a>';

    } else {

        title.textContent =
            "Sign in to EvoCrypt";

        submitButton.textContent =
            "Sign In";

        emailLabel.textContent =
            "Username";

        toggle.innerHTML =
            'New here? ' +
            '<a href="#" ' +
            'onclick="setAuthMode(\'signup\'); return false;">' +
            'Create an account</a>';
    }
}


function showError(message) {

    const error =
        document.getElementById(
            "auth-error"
        );

    error.textContent =
        message;

    error.style.display =
        "block";
}


function clearError() {

    const error =
        document.getElementById(
            "auth-error"
        );

    error.textContent =
        "";

    error.style.display =
        "none";
}


async function handleAuthSubmit(event) {

    event.preventDefault();

    clearError();


    const button =
        document.getElementById(
            "submit-btn"
        );

    button.disabled =
        true;

    button.textContent =
        "Please wait...";


    const username =
        document.getElementById(
            "email"
        ).value.trim();


    const password =
        document.getElementById(
            "password"
        ).value;


    try {

        const signup =
            authMode === "signup";


        const endpoint =
            signup
                ? "/api/register"
                : "/api/login";


        const payload =
            signup

                ? {
                    username: username,
                    email: username,
                    password: password
                }

                : {
                    username: username,
                    password: password
                };


        const response =
            await fetch(
                endpoint,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            payload
                        )
                }
            );


        const result =
            await response.json();


        if (!result.success) {

            showError(
                result.message ||
                "Authentication failed."
            );

            return;
        }


        if (signup) {

            alert(
                "Registration successful. " +
                "Sign in now."
            );

            document.getElementById(
                "password"
            ).value = "";


            setAuthMode(
                "signin"
            );

        } else {

            window.location.href =
                "/dashboard";
        }


    } catch (error) {

        console.error(
            error
        );

        showError(
            "Unable to connect to " +
            "the EvoCrypt demo server."
        );


    } finally {

        button.disabled =
            false;

        button.textContent =
            authMode === "signup"
                ? "Register"
                : "Sign In";
    }
}