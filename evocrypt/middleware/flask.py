from functools import wraps

from flask import g, jsonify, request, session


class EvoCryptFlaskMiddleware:
    """
    Flask integration layer for EvoCrypt.

    Responsibilities:
        - Validate EvoCrypt sessions
        - Track request activity
        - Expose security state to Flask
        - Protect Flask routes
        - Add baseline security headers
    """

    def __init__(
        self,
        app,
        security,
        user_session_key="user",
        evo_session_key="session_id",
    ):
        self.app = app
        self.security = security

        self.user_session_key = user_session_key
        self.evo_session_key = evo_session_key

        self._register_hooks()

    # ============================================================
    # REGISTER HOOKS
    # ============================================================

    def _register_hooks(self):
        self.app.before_request(
            self._before_request
        )

        self.app.after_request(
            self._after_request
        )

    # ============================================================
    # BEFORE REQUEST
    # ============================================================

    def _before_request(self):
        """
        Validate an EvoCrypt session before a request.
        """

        # No authenticated application session.
        # This allows login/register/public routes.
        if not session.get(
            self.user_session_key
        ):
            g.evocrypt_protected = False
            g.evocrypt_security = None

            return None

        session_id = session.get(
            self.evo_session_key
        )

        if not session_id:
            g.evocrypt_protected = False
            g.evocrypt_security = None

            return None

        # --------------------------------------------------------
        # Validate EvoCrypt session
        # --------------------------------------------------------

        try:
            valid = self.security.sessions.validate(
                session_id
            )

        except (
            KeyError,
            RuntimeError,
        ):
            valid = False

        if not valid:
            session.clear()

            return jsonify(
                {
                    "success": False,
                    "error": "EvoCrypt session expired",
                }
            ), 401

        # --------------------------------------------------------
        # Update activity
        # --------------------------------------------------------

        try:
            self.security.sessions.touch(
                session_id
            )

        except (
            KeyError,
            RuntimeError,
        ):
            session.clear()

            return jsonify(
                {
                    "success": False,
                    "error": "EvoCrypt session invalid",
                }
            ), 401

        # --------------------------------------------------------
        # Get EvoCrypt security state
        # --------------------------------------------------------

        try:
            g.evocrypt_security = (
                self.security.get_status(
                    session_id
                )
            )

        except Exception:
            g.evocrypt_security = None

        g.evocrypt_protected = True

        return None

    # ============================================================
    # AFTER REQUEST
    # ============================================================

    def _after_request(self, response):
        """
        Add baseline security headers.
        """

        response.headers.setdefault(
            "X-Content-Type-Options",
            "nosniff",
        )

        response.headers.setdefault(
            "X-Frame-Options",
            "DENY",
        )

        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )

        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )

        return response

    # ============================================================
    # PROTECTED ROUTE
    # ============================================================

    def protected(
        self,
        require_trust=None,
    ):
        """
        Protect a Flask route using EvoCrypt.

        Example:

            @middleware.protected()
            @app.route("/dashboard")
            def dashboard():
                return "Dashboard"
        """

        def decorator(function):

            @wraps(function)
            def wrapper(*args, **kwargs):

                # ------------------------------------------------
                # Check application authentication
                # ------------------------------------------------

                if not session.get(
                    self.user_session_key
                ):
                    return jsonify(
                        {
                            "success": False,
                            "error": "Authentication required",
                        }
                    ), 401

                # ------------------------------------------------
                # Get EvoCrypt session
                # ------------------------------------------------

                session_id = session.get(
                    self.evo_session_key
                )

                if not session_id:
                    return jsonify(
                        {
                            "success": False,
                            "error": "EvoCrypt session missing",
                        }
                    ), 401

                # ------------------------------------------------
                # Validate session
                # ------------------------------------------------

                if not self.security.sessions.validate(
                    session_id
                ):
                    session.clear()

                    return jsonify(
                        {
                            "success": False,
                            "error": "EvoCrypt session invalid",
                        }
                    ), 401

                # ------------------------------------------------
                # Trust requirement
                # ------------------------------------------------

                if require_trust is not None:

                    status = (
                        self.security.get_status(
                            session_id
                        )
                    )

                    score = float(
                        status.get(
                            "trust_score",
                            0,
                        )
                    )

                    if score < require_trust:
                        return jsonify(
                            {
                                "success": False,
                                "error": (
                                    "Insufficient trust score"
                                ),
                                "trust_score": score,
                                "required": require_trust,
                            }
                        ), 403

                # ------------------------------------------------
                # Update activity
                # ------------------------------------------------

                self.security.sessions.touch(
                    session_id
                )

                return function(
                    *args,
                    **kwargs
                )

            return wrapper

        return decorator

    # ============================================================
    # STATUS
    # ============================================================

    def status(self):
        """
        Return EvoCrypt status for the current Flask session.
        """

        session_id = session.get(
            self.evo_session_key
        )

        if not session_id:
            return None

        return self.security.get_status(
            session_id
        )


# ================================================================
# FLASK INITIALIZER
# ================================================================

def init_flask(
    app,
    security,
    user_session_key="user",
    evo_session_key="session_id",
):
    """
    Attach EvoCrypt to a Flask application.

    Example:

        security = EvoCrypt()

        middleware = init_flask(
            app,
            security
        )
    """

    middleware = EvoCryptFlaskMiddleware(
        app=app,
        security=security,
        user_session_key=user_session_key,
        evo_session_key=evo_session_key,
    )

    # Flask extension registry
    app.extensions[
        "evocrypt"
    ] = middleware

    return middleware