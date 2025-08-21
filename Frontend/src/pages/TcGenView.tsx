import { useState, useRef, useEffect } from "react";
import styles from "../styles/TestGenerationDashboard.module.css";

// Import your existing components
import USImportToGenerate from "../components/USImportToGenerate";
import TestFormatSelector from "../components/TestFormatSelector";

import { getOrCreateUserId } from "utils/userIDUtils";

const API_BASE = "http://localhost:8003/edge_functional_tests";

export default function TcGenView() {
  const [activeTab, setActiveTab] = useState("functional");

  // Inside your component
  const [notification, setNotification] = useState<string | null>(null);
  const [loadingDownloadFunc, setLoadingDownloadFunc] = useState(false);

  // Poll for new completed jobs
  useEffect(() => {
    let lastSeenTime = "";

    const checkForNewCompletion = async () => {
      try {
        const res = await fetch(
          `${API_BASE}/edge_func_TC/latest_completed_job`
        );
        if (!res.ok) return;
        const job = await res.json();

        if (!job || !job.started_at) return;

        // Skip if we've already seen this job
        if (lastSeenTime && job.started_at <= lastSeenTime) return;

        const launchedTime = new Date(job.started_at).toLocaleTimeString();

        if (job.status === "completed") {
          setNotification(
            `✅ Request launched at ${launchedTime} is finished!`
          );
        } else if (job.status === "failed") {
          setNotification(`❌ Request launched at ${launchedTime} failed!`);
        }

        // Auto-hide after 5 seconds
        setTimeout(() => setNotification(null), 5000);
        lastSeenTime = job.started_at;
      } catch (err) {
        console.error("Polling failed", err);
      }
    };

    // Poll every 3 seconds
    const interval = setInterval(checkForNewCompletion, 3000);
    return () => clearInterval(interval);
  }, []);

  const runTestGeneration = async () => {
    try {
      const res = await fetch(`${API_BASE}/edge_func_TC/generate/${getOrCreateUserId()}`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Request failed");
      const { started_at } = await res.json();
      const launchedTime = new Date(started_at).toLocaleTimeString();
      setNotification(`🚀 Request launched at ${launchedTime}`);
      setTimeout(() => setNotification(null), 3000);
    } catch (err) {
      setNotification("❌ Failed to launch request");
      setTimeout(() => setNotification(null), 3000);
    }
  };
  // const handleDownload = async () => {
  //   console.log("Download");
  // }

    const handleDownload = async () => {
    setLoadingDownloadFunc(true);
    try {
      const response = await fetch(`http://localhost:8003/files/edge-functional/download/${getOrCreateUserId()}`);
      if (!response.ok) {
        throw new Error("File not found");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = "Generated_TC_file.xlsx";
      link.click();

      URL.revokeObjectURL(url);
    } catch (error: any) {
      console.error("Error downloading the file:", error);
      alert("Error downloading the file. Please try again.");
    }
    finally {
      setLoadingDownloadFunc(false);
    }
  };
};



  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Dashboard de Génération de Tests</h1>

      {/* Tabs Navigation */}
      <div className={styles.tabsContainer}>
        <button
          className={`${styles.tabButton} ${
            activeTab === "functional" ? styles.activeTab : ""
          }`}
          onClick={() => setActiveTab("functional")}
        >
          Générer les Tests Fonctionnels et Non-Fonctionnels
        </button>

      </div>

      {/* Functional and Non-Functional Tests Tab */}
      {activeTab === "functional" && (
        <div className={styles.card}>
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>
              Configuration des Tests Fonctionnels
            </h3>
            <USImportToGenerate />
            <TestFormatSelector />
          </div>
          <div className={styles.section} style={{ padding: "2rem" }}>
           
              <h3 className={styles.sectionTitle}>
                Génération des Cas de Test
              </h3>
              <center>
              {/* Button to Launch Generation */}
              <button
                className={styles.button}
                onClick={runTestGeneration}
                style={{
                  padding: "10px 20px",
                  fontSize: "16px",
                  backgroundColor: "#007bff",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                  margin: "0.5rem",
                }}
                disabled={false}
              >
                Lancer la Génération
              </button>

              {/* Button to Download */}
              <button
                className={styles.buttonSecondary}
                onClick={handleDownload}
                disabled={loadingDownloadFunc}                
              >
                {loadingDownloadFunc
                  ? "Téléchargement..."
                  : "Télécharger les Cas de Test Générés"}
              </button>

              {/* Toggle Notification */}
              {notification && (
                <div
                  style={{
                    position: "fixed",
                    bottom: "20px",
                    right: "20px",
                    background: "white",
                    border: "1px solid #ddd",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                    padding: "12px 16px",
                    borderRadius: "8px",
                    fontSize: "14px",
                    maxWidth: "300px",
                    zIndex: 1000,
                    animation: "fadeIn 0.3s ease-out",
                  }}
                >
                  {notification}
                </div>
              )}
            </center>
          </div>
        </div>
      )}

    </div>
  );
}
