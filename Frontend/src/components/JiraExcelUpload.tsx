import { useState } from "react";
import styles from "../styles/UserStoriesForm.module.css";

export default function JiraExcelUpload() {
  const [jiraProjectKey, setJiraProjectKey] = useState("");
  const [stateFieldName, setStateFieldName] = useState("");
  const [excelFiles, setExcelFiles] = useState<File[]>([]);
  const [appLink, setAppLink] = useState("");

  const handleUpload = async () => {
    if (!jiraProjectKey || !stateFieldName || !appLink) {
      alert("Please fill in all fields and upload at least one file.");
      return;
    }
    console.log("Jira Project Key:", jiraProjectKey); 

    const formData = new FormData();
    formData.append("jira_project_key", jiraProjectKey);
    formData.append("state_field_name", stateFieldName);
    excelFiles.forEach(file => formData.append("excelFiles", file));
    formData.append("app_link", appLink);

    try {
      const response = await fetch("http://localhost:8004/upload-jira-excels", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      console.log("Server Response:", result); // Log the server response for debugging
      alert(result.message || "Upload successful!");
    } catch (error) {
      console.error("Upload error:", error);
      alert("An error occurred during upload.");
    }
  };

  return (
    <div className={styles.card}>
      <h3>Upload Jira Data and Test Data Excel Files</h3>

      <label className={styles.label}>Jira Project Key</label>
      <input
        type="text"
        placeholder="PROJ"
        value={jiraProjectKey}
        onChange={(e) => setJiraProjectKey(e.target.value)}
        className={styles.inputField}
      />

      <label className={styles.label}>Jira State Field (of Test Cases) </label>
      <input
        type="text"
        placeholder="status"
        value={stateFieldName}
        onChange={(e) => setStateFieldName(e.target.value)}
        className={styles.inputField}
      />

      <label className={styles.label}>Upload Test Data Excel Files</label>
      <input
        type="file"
        accept=".xlsx,.xls"
        multiple
        onChange={(e) => setExcelFiles(Array.from(e.target.files || []))}
        className={styles.inputField}
      />

      <label className={styles.label}>Application Link</label>
      <input
        type="text"
        placeholder="http://example.com"
        value={appLink}
        onChange={(e) => setAppLink(e.target.value)}
        className={styles.inputField}
      />

      <button onClick={handleUpload} className={styles.button}>
        Upload
      </button>
    </div>
  );
}
