import { useState } from "react";
import axios from "axios";
import styles from "../styles/UserStoriesForm.module.css";
import { useJira } from "./JiraContext";
import { getOrCreateUserId } from "utils/userIDUtils";

export default function TCHistoryForm() {
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [jiraProjectKey, setJiraProjectKey] = useState("");
  const [uploading, setUploading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [graphCreated, setGraphCreated] = useState(false);

  // Get saved Jira configurations from context
  const { configs } = useJira();

  // Flatten and deduplicate all project keys across configurations
  const allProjectKeys = Array.from(
    new Set(configs.flatMap((config) => config.projectKeys))
  ).sort();

  // Handle file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setExcelFile(file);
    setMessage(""); // Clear previous messages
    setError("");
  };

  // Upload Excel or Jira project data
  const handleUpload = async () => {
    if (!excelFile && !jiraProjectKey) {
      setError("Please upload an Excel file or select a Jira project.");
      setMessage("");
      return;
    }

    const formData = new FormData();
    if (excelFile) formData.append("file", excelFile);
    if (jiraProjectKey) formData.append("jira_project_key", jiraProjectKey);
    formData.append("user_id", getOrCreateUserId());

    try {
      setUploading(true);
      setError("");
      setMessage("");

      const response = await fetch(
        "http://localhost:8000/api/files/test-cases/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      const result = await response.json();
      if (!response.ok) {
        setError(`Upload failed: ${result.detail}`);
      } else {
        setMessage(result.message || "Succès Upload !");
        console.log(result);
        alert(`Import successful: ${result.message}`);
      }
    } catch (error) {
      console.error("Upload error:", error);
      setMessage("Une erreur s'est produite lors de l'upload.");
      const errorMessage =
        error instanceof Error ? error.message : "An unknown error occurred";
      alert(`Import failed: ${errorMessage}`);
    } finally {
      setUploading(false);
    }
  };

  // Create the graph
  const handleCreate = async () => {
    try {
      setCreating(true);
      setError("");
      setMessage("Creating graph... Cela pourrait prendre un certain temps.");

      // const response = await axios.post("http://localhost:8000/api/graphs/test-cases/create");

      const response = await axios.post(
        `http://localhost:8000/api/graphs/test-cases/create/${jiraProjectKey}`
      );
      setMessage("Graph created successfully!");
      setGraphCreated(true);
      console.log(response.data);
    } catch (error: any) {
      setError(
        error?.response?.data?.detail ||
          "Échec de la création du graphe. Veuillez vérifier les journaux du serveur pour plus de détails."
      );
      setMessage("");
      console.error(error);
    } finally {
      setCreating(false);
    }
  };

  // Update the graph
  const handleUpdate = async () => {
    if (!excelFile && !jiraProjectKey) {
      setError("Please provide a file or select a Jira project to update.");
      setMessage("");
      return;
    }

    try {
      setUpdating(true);
      setError("");
      setMessage("Updating graph... Cela pourrait prendre un certain temps.");

      const formData = new FormData();
      if (excelFile) formData.append("file", excelFile);
      if (jiraProjectKey) formData.append("jira_project_key", jiraProjectKey);

      const response = await fetch(
        `http://localhost:8000/api/graphs/test-cases/update/${jiraProjectKey}/${getOrCreateUserId()}`,
        {
          method: "POST",
          body: formData,
        }
      );

      const result = await response.json();
      if (!response.ok) {
        setError(`Update failed: ${result.detail}`);
        setMessage("");
      } else {
        setMessage("Succès update Graphe !");
        setGraphCreated(true);
      }
    } catch (error: any) {
      setError(
        "Échec de la mise à jour du graphe. Veuillez vérifier les journaux du serveur pour plus de détails."
      );
      setMessage("");
      console.error(error);
    } finally {
      setUpdating(false);
    }
  };

  // Open visualizer in new tab 
  const handleRedirect = () => {
    if (!jiraProjectKey) {
      setError(
        "Veuillez sélectionner un projet JIRA avant de visualiser le graphe."
      );
      return;
    }

    const url = `http://localhost:3001/graphrag-visualizer#/graph?projectId=${encodeURIComponent(
      jiraProjectKey
    )}&graphId=test_case_graph`;

    window.open(url, "_blank", "noopener,noreferrer");
  };


  return (
    <div className={styles.card}>
      <h3>Historique des Cas de Test</h3>
      {/* Jira Project Selection */}
      <label className={styles.label}>Selectionner Projet Jira</label>
      {allProjectKeys.length > 0 ? (
        <select
          value={jiraProjectKey}
          onChange={(e) => setJiraProjectKey(e.target.value)}
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
          Aucun projet Jira enregistré. Configurez vos projets dans les
          paramètres.
        </p>
      )}

      {/* Excel File Upload */}
      <label className={styles.label}>
        Télécharger un fichier Excel (.xlsx, .xls)
      </label>
      <label className={styles.fileUpload}>
        <input
          type="file"
          accept=".xlsx,.xls"
          onChange={handleFileChange}
          disabled={uploading}
          style={{ display: "none" }}
        />
        {excelFile ? (
          <span title={excelFile.name} className="truncate">
            📄 {excelFile.name}
          </span>
        ) : (
          "📂 Choose Excel File"
        )}
      </label>
      <p className={styles.hint}>Max 10MB – .xlsx or .xls only</p>

      {/* Action Buttons */}
      <button
        onClick={handleUpload}
        className={styles.button}
        disabled={uploading}
      >
        {uploading ? "📤 Uploading..." : "Charger Jira ou Fichier"}
      </button>

      <button
        onClick={handleCreate}
        className={styles.button}
        disabled={uploading || creating || graphCreated}
      >
        {creating
          ? "⏳ Creating..."
          : graphCreated
          ? "✅ Created"
          : "Créer le Graphe"}
      </button>

      <button
        onClick={handleUpdate}
        className={styles.button}
        disabled={uploading || updating}
      >
        {updating ? "🔄 Updating..." : "Mettre à jour le graphe"}
      </button>

      <button
        onClick={handleRedirect}
        className={`${styles.button} ${
          !graphCreated ? styles.buttonDisabled : ""
        }`}
        disabled={!graphCreated}
      >
        🌐 Visualiser le graphe des Tests
      </button>

      {/* Messages */}
      {message && <p className={styles.message}>{message}</p>}
      {error && <p className={styles.errorMessage}>{error}</p>}
    </div>
  );
}
