import { useState } from "react";
import axios from "axios";
import styles from "../styles/UserStoriesForm.module.css";
import { useJira } from "./JiraContext";
import { getOrCreateUserId } from "../utils/userIDUtils";

export default function UserStoriesForm() {
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [jiraProjectKey, setJiraProjectKey] = useState("");
  const [uploading, setUploading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [uploadCompleted, setUploadCompleted] = useState(false); // ✅ Track upload state
  const [graphCreated, setGraphCreated] = useState(false);
    const [updating, setUpdating] = useState(false);

  // Get saved Jira configs
  const { configs } = useJira();

  // Flatten all project keys from all saved connections
  const allProjectKeys = Array.from(
    new Set(configs.flatMap((config) => config.projectKeys))
  ).sort();

  // Handle file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setExcelFile(file);
    setMessage("");
    setError("");
    setUploadCompleted(false); // Reset on new file
  };

  const handleUpload = async () => {
    if (!excelFile && !jiraProjectKey) {
      setError("Please upload a file or select a Jira project.");
      setMessage("");
      return;
    }

    const formData = new FormData();
    if (excelFile) formData.append("file", excelFile);
    if (jiraProjectKey) formData.append("jira_project_key", jiraProjectKey);
    formData.append("user_id", getOrCreateUserId());
    console.log(getOrCreateUserId());

    try {
      setUploading(true);
      setError("");
      setMessage(`Uploading ${excelFile ? "file" : "Jira data"}...`);

      const response = await fetch(
        "http://localhost:8000/api/files/epics-features-us/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      const result = await response.json();
      if (!response.ok) {
        setError(`Upload failed: ${result.detail}`);
        setMessage("");
      } else {
        setMessage(result.message || "Upload successful!");
        setUploadCompleted(true); // ✅ Mark as completed
        console.log(result);
      }
    } catch (err) {
      console.error("Upload error:", err);
      setError("An error occurred during upload.");
      setMessage("");
    } finally {
      setUploading(false);
    }
  };

  // const handleCreate = async () => {
  //   // ✅ Allow graph creation if upload is complete OR Jira project is selected
  //   if (!uploadCompleted && !jiraProjectKey) {
  //     setError("Please upload a file or load Jira data first.");
  //     return;
  //   }

  //   try {
  //     setCreating(true);
  //     setError("");
  //     setMessage("Creating graph... This may take a moment.");

  //     const response = await axios.post(
  //       "http://localhost:8000/api/graphs/user-stories/create"
  //     );
  //     setMessage("Graph created successfully!");
  //     setGraphCreated(true);
  //     console.log(response.data);
  //   } catch (err: any) {
  //     setError(
  //       err?.response?.data?.detail ||
  //         "Failed to create graph. Check server logs."
  //     );
  //     setMessage("");
  //     console.error(err);
  //   } finally {
  //     setCreating(false);
  //   }
  // };

  const handleCreate = async () => {
    // ✅ Allow graph creation if upload is complete OR Jira project is selected
    if (!uploadCompleted && !jiraProjectKey) {
      setError("Please upload a file or load Jira data first.");
      return;
    }

    try {
      setCreating(true);
      setError("");
      setMessage("Creating graph... This may take a moment.");

      // 🔐 Get the persistent user ID
      const userId = getOrCreateUserId();

      const formData = new FormData();
      formData.append("jira_project_key", jiraProjectKey);
      formData.append("user_id", userId);

      const response = await axios.post(
        "http://localhost:8000/api/graphs/user-stories/create",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      setMessage("Graph created successfully!");
      setGraphCreated(true);
      console.log("Graph creation response:", response.data);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          "Failed to create graph. Check server logs."
      );
      setMessage("");
      console.error("Graph creation error:", err);
    } finally {
      setCreating(false);
    }
  };

  
  const handleUpdate = async () => {
    try {
      setUpdating(true);
      setError("");
      setMessage("Updating graph... Cela pourrait prendre un certain temps.");

      const formData = new FormData();
      if (excelFile) formData.append("file", excelFile);
      if (jiraProjectKey) formData.append("jira_project_key", jiraProjectKey);

      const response = await fetch(`http://localhost:8000/api/graphs/user-stories/update/${jiraProjectKey}/${getOrCreateUserId()}`, {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      if (!response.ok) {
        setError(`Update failed: ${result.detail}`);
        setMessage("");
      } else {
        setMessage("Succès update Graphe !");
        console.log(result);
      }
    } catch (error: any) {
      setError("Échec de la mise à jour du graphe. Veuillez vérifier les journaux du serveur pour plus de détails.");
      setMessage("");
      console.error(error);
    } finally {
      setUpdating(false);
    }
  };
 
  const handleRedirect = () => {
    const userId = getOrCreateUserId(); // Utilisé comme graphId
    if (!jiraProjectKey || !userId) {
      setError("Impossible d’ouvrir la visualisation : données manquantes.");
      return;
    }

    const url = `http://localhost:3001/graphrag-visualizer#/graph?projectId=${jiraProjectKey}&graphId=us_graph`;
    window.open(url, "_blank");
  };

  return (
    <div className={styles.card}>
      <h3>Données des User Stories</h3>

      {/* Jira Project Selection */}
      <label className={styles.label}>Selectionner Projet Jira</label>
      {allProjectKeys.length > 0 ? (
        <select
          value={jiraProjectKey}
          onChange={(e) => {
            setJiraProjectKey(e.target.value);
            setUploadCompleted(false); // Reset if project changes
            setMessage("");
            setError("");
          }}
          className={styles.inputField}
          disabled={uploading}
        >
          <option value="">-- Choisir un projet --</option>
          {allProjectKeys.map((key) => (
            <option key={key} value={key}>
              {key}
            </option>
          ))}
        </select>
      ) : (
        <p className={styles.hint}>
          Aucun projet Jira enregistré. Configurez vos projets dans les paramètres.
        </p>
      )}

      {/* File Upload */}
      <label className={styles.label}>Télécharger un fichier Excel (.xlsx, .xls)</label>
      <label className={styles.fileUpload}>
        <input
          type="file"
          accept=".xlsx,.xls"
          onChange={handleFileChange}
          disabled={uploading}
          style={{ display: "none" }}
        />
        {excelFile ? (
          <span
            title={excelFile.name}
            style={{
              display: "block",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            📄 {excelFile.name}
          </span>
        ) : (
          "📂 Choose Excel File"
        )}
      </label>

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        className={styles.button}
        disabled={uploading || (!excelFile && !jiraProjectKey)}
      >
        {uploading ? "📤 Uploading..." : "Charger Jira ou Fichier"}
      </button>

      {/* Create Graph Button */}
      <button
        onClick={handleCreate}
        className={styles.button}
        disabled={creating || (!uploadCompleted && !jiraProjectKey)}
      >
        {creating
          ? "⏳ Creating..."
          : graphCreated
          ? "✅ Graph Created"
          : "Créer Graphe US Epic"}
      </button>

      <button
        onClick={handleUpdate}
        className={styles.button}
        disabled={uploading || updating}
      >
        {updating ? "🔄 Updating..." : "Mettre à jour le graphe"}
      </button>

      {/* Visualize Button */}
      <button
        onClick={handleRedirect}
        className={`${styles.button} ${
          !graphCreated ? styles.buttonDisabled : ""
        }`}
        disabled={!graphCreated}
      >
        🌐 Visualiser le graphe des US
      </button>

      {/* Messages */}
      {message && <p className={styles.message}>{message}</p>}
      {error && <p className={styles.errorMessage}>{error}</p>}
    </div>
  );
}
