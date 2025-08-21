import { useState } from "react";
import styles from "../styles/UserStoriesForm.module.css";
import { useJira } from "./JiraContext"; // Make sure this is correct path
import { getOrCreateUserId } from "utils/userIDUtils";

export default function USImportToGenerate() {
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [jiraProjectKey, setJiraProjectKey] = useState("");
  const [sourceStateFieldName, setSourceStateFieldName] = useState("");
  const [targetStateFieldName, setTargetStateFieldName] = useState("");
  const [sprint, setSprint] = useState("");
  const [etiquette, setEtiquette] = useState("");
  const [assignee, setAssignee] = useState("");
  const [message, setMessage] = useState("");
  const [uploading, setUploading] = useState(false);
  const [importing, setImporting] = useState(false);

  // Use Jira context to get project keys
  const { configs } = useJira();
  const allProjectKeys = Array.from(
    new Set(configs.flatMap((config) => config.projectKeys))
  ).sort();

  // Handle file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setExcelFile(file);
    setMessage(""); // Clear previous message
  };

  // Upload handler
  const handleUpload = async () => {
    if (
      !excelFile &&
      (!jiraProjectKey ||
        !sourceStateFieldName ||
        !targetStateFieldName ||
        !sprint ||
        !assignee)
    ) {
      setMessage("Please upload an Excel file or provide Jira information.");
      return;
    }

    const formData = new FormData();
    if (excelFile) formData.append("file", excelFile);
    if (jiraProjectKey) formData.append("jira_project_key", jiraProjectKey);
    if (sourceStateFieldName)
      formData.append("source_state_field_name", sourceStateFieldName);
    if (targetStateFieldName)
      formData.append("target_state_field_name", targetStateFieldName);
    if (sprint) formData.append("sprint", sprint);
    if (etiquette) formData.append("etiquette", etiquette);
    if (assignee) formData.append("assignee", assignee);
    formData.append("user_id", getOrCreateUserId());

    try {
      setUploading(true);
      setMessage("");

      const response = await fetch(
        "http://localhost:8003/files/user-stories-to-generate/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      const result = await response.json();
      if (!response.ok) {
        setMessage(`Upload failed: ${result.detail}`);
      } else {
        setMessage(result.message || "Upload successful!");
        console.log(result);
      }
    } catch (error) {
      console.error("Upload error:", error);
      setMessage("An error occurred during upload.");
    } finally {
      setUploading(false);
    }
  };

  // Import handler
  const handleUSImport = async () => {
    setImporting(true);
    try {
      const response = await fetch(
        `http://localhost:8003/files/user-stories-to-generate/import/${jiraProjectKey}/${getOrCreateUserId()}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();
      alert(
        `Successfully imported ${data.total_user_stories} user stories from ${data.data_source}`
      );
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      alert(`Import failed: ${errorMessage}`);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className={styles.cardWide}>
      <h3>Importation des User Stories</h3>

      {/* Styled File Upload */}
      <label className={styles.label}>
        Importer fichier Excel de Stories (.xlsx, .xls)
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
      <p className={styles.hint}>Max 10MB – .xlsx or .xls only</p>

      {/* Jira Project Selection */}
      <label className={styles.label}>Select Jira Project (optional)</label>
      {allProjectKeys.length > 0 ? (
        <select
          value={jiraProjectKey}
          onChange={(e) => setJiraProjectKey(e.target.value)}
          className={styles.inputField}
          disabled={uploading}
        >
          <option value="">-- Choose a project --</option>
          {allProjectKeys.map((key) => (
            <option key={key} value={key}>
              {key}
            </option>
          ))}
        </select>
      ) : (
        <p className={styles.hint}>
          No Jira projects saved. Go to Settings to connect.
        </p>
      )}

      {/* Source State Field */}
      <label className={styles.label}>
        État Story à extraire de Jira (optional)
      </label>
      <input
        type="text"
        placeholder="e.g., 'To Do', 'En cours'"
        value={sourceStateFieldName}
        onChange={(e) => setSourceStateFieldName(e.target.value)}
        className={styles.inputField}
        disabled={uploading}
      />

      {/* Target State Field */}
      <label className={styles.label}>
        État Tests Cases à exporter à Jira (optional)
      </label>
      <input
        type="text"
        placeholder="e.g., 'Done', 'Terminé'"
        value={targetStateFieldName}
        onChange={(e) => setTargetStateFieldName(e.target.value)}
        className={styles.inputField}
        disabled={uploading}
      />

      {/* Sprint */}
      <label className={styles.label}>Sprint (optional)</label>
      <input
        type="text"
        placeholder="e.g., Sprint 1"
        value={sprint}
        onChange={(e) => setSprint(e.target.value)}
        className={styles.inputField}
        disabled={uploading}
      />

      {/* Assignee */}
      <label className={styles.label}>Personne Assignée (optional)</label>
      <input
        type="text"
        placeholder="e.g., john.doe@company.com"
        value={assignee}
        onChange={(e) => setAssignee(e.target.value)}
        className={styles.inputField}
        disabled={uploading}
      />

      {/* Etiquette */}
      <label className={styles.label}>Etiquette (optional)</label>
      <input
        type="text"
        placeholder="e.g., us-import-2025"
        value={etiquette}
        onChange={(e) => setEtiquette(e.target.value)}
        className={styles.inputField}
        disabled={uploading}
      />

      {/* Action Buttons */}
      <button
        onClick={handleUpload}
        className={styles.button}
        disabled={uploading}
      >
        {uploading ? "📤 Uploading..." : "Charger Jira ou Fichier"}
      </button>

      <button
        onClick={handleUSImport}
        className={styles.button}
        disabled={importing}
      >
        {importing ? "🔄 Importing..." : "Importer User Stories"}
      </button>

      {/* Messages */}
      {message && <p className={styles.message}>{message}</p>}
    </div>
  );
}
