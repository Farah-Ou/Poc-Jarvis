


import { useState } from "react";
import styles from "../styles/UserStoriesForm.module.css";

export default function SimpleExcelAndAppLink() {
  const [excelGherkin, setExcelGherkin] = useState<File[]>([]);
  const [excelTestData, setExcelTestData] = useState<File[]>([]);
  const [appLink, setAppLink] = useState("");

  const handleUpload = async () => {
    if ((!excelGherkin.length && !excelTestData.length) || !appLink) {
      alert("Please upload files and provide the application link.");
      return;
    }

    const formData = new FormData();
    excelGherkin.forEach(file => formData.append("excelGherkin", file));
    excelTestData.forEach(file => formData.append("excelTestData", file));
    formData.append("app_link", appLink);

    try {
      const response = await fetch("http://localhost:8004/upload-jira-excels", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      alert(result.message || "Upload successful!");
    } catch (error) {
      console.error("Upload error:", error);
      alert("An error occurred during upload.");
    }
  };

  return (
    <div className={styles.card}>
      <h3>Upload Files Manually</h3>

      <label className={styles.label}>Upload Gherkin Test Cases Excel Files</label>
      <input
        type="file"
        accept=".xlsx,.xls"
        multiple
        onChange={(e) => setExcelGherkin(Array.from(e.target.files || []))}
        className={styles.inputField}
      />

      <label className={styles.label}>Upload Test Data Excel Files</label>
      <input
        type="file"
        accept=".xlsx,.xls"
        multiple
        onChange={(e) => setExcelTestData(Array.from(e.target.files || []))}
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
