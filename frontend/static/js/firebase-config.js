// ---------------------------------------------------------------------------
// Firebase web app configuration
//
// Get these values from: Firebase console > Project settings > General >
// "Your apps" > SDK setup and configuration > Config.
//
// This file is safe to expose to the browser - it is not a secret, it just
// tells the Firebase SDK which project to talk to. Access is controlled by
// Firebase Authentication + your security rules, not by hiding these values.
// ---------------------------------------------------------------------------
const firebaseConfig = {
  apiKey: "REPLACE_WITH_YOUR_API_KEY",
  authDomain: "REPLACE_WITH_YOUR_PROJECT.firebaseapp.com",
  projectId: "REPLACE_WITH_YOUR_PROJECT_ID",
  storageBucket: "REPLACE_WITH_YOUR_PROJECT.appspot.com",
  messagingSenderId: "REPLACE_WITH_YOUR_SENDER_ID",
  appId: "REPLACE_WITH_YOUR_APP_ID"
};

// Set to true once the values above are filled in with a real project.
// While false, the login page uses the local demo account instead
// (admin / password123) so the app keeps working out of the box.
const FIREBASE_CONFIGURED = false;

if (typeof firebase !== 'undefined' && FIREBASE_CONFIGURED) {
  firebase.initializeApp(firebaseConfig);
}
