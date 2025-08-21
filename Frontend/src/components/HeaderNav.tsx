import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import styles from "../styles/HeaderNav.module.css";
import { useJira } from "./JiraContext"; // Import hook
import { getOrCreateUserId } from "utils/userIDUtils";

export default function HeaderNav() {
  const [showPopup, setShowPopup] = useState(false);
  const [serverUrl, setServerUrl] = useState("");
  const [username, setUsername] = useState("");
  const [jiraProjectKey, setJiraProjectKey] = useState("");
  const [connectionStatus, setConnectionStatus] = useState<
    "idle" | "success" | "failure"
  >("idle");

  const { addOrUpdateConfig } = useJira(); // Get function from context

  const handleConnect = async () => {
    if (!serverUrl || !username || !jiraProjectKey) {
      setConnectionStatus("failure");
      return;
    }

    try {
      const bodyToSend = JSON.stringify({
        jira_server_url: serverUrl.trim(),
        jira_username: username.trim(),
        jira_project_key: jiraProjectKey.trim(), 
        user_id: getOrCreateUserId(),
      });

      console.log("Sending:", bodyToSend);

      const response = await fetch(
        "http://127.0.0.1:8000/api/jira/upload-jira-credentials",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: bodyToSend,
        }
      );

      if (response.ok) {
        // Save to context (and localStorage)
        addOrUpdateConfig(
          serverUrl.trim(),
          username.trim(),
          jiraProjectKey.trim()
        );
        setConnectionStatus("success");
      } else {
        const error = await response.text();
        console.error("API Error:", error);
        setConnectionStatus("failure");
      }
    } catch (error) {
      console.error("Connection error:", error);
      setConnectionStatus("failure");
    }
  };

  return (
    <nav className={styles.navContainer}>
      {/* Left side: Navigation Links */}
      <div className={styles.navLinks}>
        <NavLink
          to="/"
          className={({ isActive }) =>
            `${styles.navButton} ${styles.homeButton} ${
              isActive ? styles.active : ""
            }`
          }
        >
          Home
        </NavLink>
        <NavLink
          to="/tcgen"
          className={({ isActive }) =>
            `${styles.navButton} ${isActive ? styles.active : ""}`
          }
        >
          Tests Generator
        </NavLink>
      </div>

      {/* Right side: Logo + Gear Icon */}
      <div className={styles.logoContainer}>
        <button
          type="button"
          className={styles.gearButton}
          onClick={() => setShowPopup(!showPopup)}
          aria-label="Open settings"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            width="20"
            height="20"
          >
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1.51-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0 .33 1.82 1.65 1.65 0 0 0 1.51 1.51H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09z" />
          </svg>
        </button>

        {showPopup && (
          <div
            className={styles.popupOverlay}
            onClick={() => setShowPopup(false)}
          >
            <div
              className={styles.popupContent}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Close Button */}
              <button
                className={styles.closeButton}
                onClick={() => setShowPopup(false)}
                aria-label="Close"
              >
                ✕
              </button>

              <h3 style={{ textAlign: "center", marginBottom: "20px" }}>
                Connect to Jira
              </h3>

              <div className={styles.formGroup}>
                <label htmlFor="serverUrl">Server URL</label>
                <input
                  type="url"
                  id="serverUrl"
                  value={serverUrl}
                  onChange={(e) => setServerUrl(e.target.value)}
                  placeholder="https://your-domain.atlassian.net"
                  required
                />
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="username">Username (Email)</label>
                <input
                  type="text"
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="you@example.com"
                  required
                />
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="jiraProjectKey">Project Key</label>
                <input
                  type="text"
                  id="jiraProjectKey"
                  value={jiraProjectKey}
                  onChange={(e) => setJiraProjectKey(e.target.value)}
                  placeholder="e.g. PROJ"
                  required
                />
              </div>

              {connectionStatus === "success" && (
                <p className={styles.successMessage}>✅ Connected and saved!</p>
              )}
              {connectionStatus === "failure" && (
                <p className={styles.errorMessage}>
                  ❌ Failed. Check URL, username, or key.
                </p>
              )}

              <div className={styles.formActions}>
                <button type="button" onClick={handleConnect}>
                  Connect & Save
                </button>
              </div>
            </div>
          </div>
        )}

        <img src="/talan.png" alt="Talan Logo" className={styles.logo} />
      </div>
    </nav>
  );
}
