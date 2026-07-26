// Handles both real Firebase auth and the local demo fallback, so the
// login screen behaves the same way regardless of which mode is active.

let authMode = 'signin'; // 'signin' | 'signup'

function setAuthMode(mode) {
  authMode = mode;
  const toggle = document.getElementById('auth-toggle-text');
  const submitBtn = document.getElementById('submit-btn');
  const title = document.getElementById('form-title');
  if (mode === 'signup') {
    title.textContent = 'Create your account';
    submitBtn.textContent = 'Create account';
    toggle.innerHTML = 'Already have an account? <a href="#" onclick="setAuthMode(\'signin\'); return false;">Sign in</a>';
  } else {
    title.textContent = 'Sign in to EvoCrypt';
    submitBtn.textContent = 'Sign in';
    toggle.innerHTML = "New here? <a href=\"#\" onclick=\"setAuthMode('signup'); return false;\">Create an account</a>";
  }
  clearError();
}

function showError(message) {
  const el = document.getElementById('auth-error');
  el.textContent = message;
  el.style.display = 'block';
}

function clearError() {
  const el = document.getElementById('auth-error');
  el.style.display = 'none';
  el.textContent = '';
}

function setLoading(isLoading) {
  const btn = document.getElementById('submit-btn');
  btn.disabled = isLoading;
  btn.textContent = isLoading ? 'Verifying…' : (authMode === 'signup' ? 'Create account' : 'Sign in');
}

async function sendSessionToBackend(payload) {
  const response = await fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return response.json();
}

async function handleAuthSubmit(event) {
  event.preventDefault();
  clearError();

  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;

  if (!email || !password) {
    showError('Enter both an email/username and a password.');
    return;
  }

  setLoading(true);

  try {
    if (typeof FIREBASE_CONFIGURED !== 'undefined' && FIREBASE_CONFIGURED) {
      // --- Real Firebase path ---
      let userCredential;
      if (authMode === 'signup') {
        userCredential = await firebase.auth().createUserWithEmailAndPassword(email, password);
      } else {
        userCredential = await firebase.auth().signInWithEmailAndPassword(email, password);
      }
      const idToken = await userCredential.user.getIdToken();
      const result = await sendSessionToBackend({ idToken });

      if (result.success) {
        window.location.href = '/dashboard';
      } else {
        showError(result.message || 'Sign-in failed.');
      }
    } else {
      // --- Demo fallback path (no Firebase project configured yet) ---
      const result = await sendSessionToBackend({ username: email, password });
      if (result.success) {
        window.location.href = '/dashboard';
      } else {
        showError(result.message || 'Invalid credentials.');
      }
    }
  } catch (err) {
    showError(humanizeAuthError(err));
  } finally {
    setLoading(false);
  }
}

function humanizeAuthError(err) {
  const code = err && err.code;
  const map = {
    'auth/email-already-in-use': 'That email already has an account. Try signing in instead.',
    'auth/invalid-email': 'That email address looks invalid.',
    'auth/weak-password': 'Choose a password with at least 6 characters.',
    'auth/user-not-found': 'No account found with that email.',
    'auth/wrong-password': 'Incorrect password.',
    'auth/invalid-credential': 'Incorrect email or password.'
  };
  return map[code] || (err && err.message) || 'Something went wrong. Try again.';
}
