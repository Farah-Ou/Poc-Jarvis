import { useState } from "react";
import axios from "axios";
import styles from "../styles/BusinessDomainForm.module.css";

export default function BusinessDomainForm() {
  const [businessFiles, setBusinessFiles] = useState<FileList | null>(null);
  const [guidelinesFiles, setGuidelinesFiles] = useState<FileList | null>(null);
  const [uploading, setUploading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [graphCreated, setGraphCreated] = useState(false);

  const handleUpload = async () => {
    if (!businessFiles && !guidelinesFiles) {
      setMessage("Please upload at least one file.");
      return;
    }

    const formData = new FormData();
    if (businessFiles) {
      Array.from(businessFiles).forEach((file) => {
        formData.append("business_domain_files", file);
      });
    }
    if (guidelinesFiles) {
      Array.from(guidelinesFiles).forEach((file) => {
        formData.append("company_guidelines_files", file);
      });
    }

    try {
      setUploading(true);
      setMessage("");
      setError("");

      await axios.post("http://localhost:8000/upload-documents/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setMessage("Upload successful!");
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.detail ||
        "Upload failed. Please check the files or server.";
      setError(errorMsg);
      console.error("Upload error:", err);
    } finally {
      setUploading(false);
    }
  };

  const handleCreate = async () => {
    try {
      setCreating(true);
      setMessage("");
      setError("");

      const response = await axios.post(
        "http://localhost:8000/api/graphs/guidelines/create"
      );
      setMessage("Graph created successfully!");
      setGraphCreated(true);
      console.log(response.data);
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.detail ||
        "Failed to create graph. Check server logs.";
      setError(errorMsg);
      console.error("Graph creation error:", err);
    } finally {
      setCreating(false);
    }
  };

  const handleRedirect = () => {
    window.open("http://localhost:3003/graphrag-visualizer", "_blank");
  };

  return (
    <div className={styles.card}>
      <h3 className="text-center font-medium">Business Domain & Guidelines</h3>

      {/* Business Domain Files */}
      <label className={styles.label}>Business Domain Files (.pdf, .txt)</label>
      <label className={styles.fileUpload}>
        📂 Choose Business Files
        <input
          type="file"
          accept=".pdf,.txt"
          multiple
          onChange={(e) => setBusinessFiles(e.target.files)}
          disabled={uploading}
        />
      </label>

      {/* Company Guidelines Files */}
      <label className={styles.label}>
        Company Guidelines Files (.pdf, .txt)
      </label>
      <label className={styles.fileUpload}>
        📂 Choose Guidelines Files
        <input
          type="file"
          accept=".pdf,.txt"
          multiple
          onChange={(e) => setGuidelinesFiles(e.target.files)}
          disabled={uploading}
        />
      </label>

      {/* Action Buttons */}
      <button
        onClick={handleUpload}
        className={styles.button}
        disabled={uploading}
      >
        {uploading ? "Uploading..." : "Upload Files"}
      </button>

      <button
        onClick={handleCreate}
        className={styles.button}
        disabled={uploading || creating}
      >
        {creating ? "Creating..." : "Create Graph"}
      </button>

      <button
        onClick={handleRedirect}
        className={`${styles.button} ${
          !graphCreated ? styles.buttonDisabled : ""
        }`}
        disabled={!graphCreated}
      >
        Visualiser le graphe de Guidelines
      </button>

      {/* Messages */}
      {message && <p className={styles.message}>{message}</p>}
      {error && <p className={styles.errorMessage}>{error}</p>}
    </div>
  );
}
