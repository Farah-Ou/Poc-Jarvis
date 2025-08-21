import { useState } from "react";
import axios from "axios";
import styles from "../styles/BusinessDomainForm.module.css";

export default function SpecFilesForm() {
  const [specFiles, setSpecFiles] = useState<FileList | null>(null);
  const [uploading, setUploading] = useState(false);
  const [creating, setCreating] = useState(false);
  // const [visualizing, setVisualizing] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [graphCreated, setGraphCreated] = useState(false);

  const handleUpload = async () => {
    if (!specFiles || specFiles.length === 0) {
      setError("Please select specification files to upload.");
      setMessage("");
      return;
    }
    
    const formData = new FormData();
    for (const file of Array.from(specFiles)) {
      formData.append("files", file);
    }
    
    try {
      setUploading(true);
      setError("");
      setMessage("Uploading files...");
      
      const response = await axios.post("http://localhost:8000/upload-spec-files/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      
      setMessage(`Successfully uploaded ${specFiles.length} file(s).`);
      console.log(response.data);
    } catch (error: any) {
      setError(error?.response?.data?.detail || "Upload failed. Please try again.");
      setMessage("");
      console.error(error);
    } finally {
      setUploading(false);
    }
  };

  const handleCreate = async () => {
    try {
      setCreating(true);
      setError("");
      setMessage("Creating graph... This may take a moment.");
     
      // Call the backend to create the graph
      const response = await axios.post("http://localhost:8000/api/graphs/spec/create");
     
      setMessage("Graph created successfully!");
      setGraphCreated(true);
      console.log(response.data);
    } catch (error: any) {
      setError(error?.response?.data?.detail || "Failed to create graph. Please check server logs for details.");
      setMessage("");
      console.error(error);
    } finally {
      setCreating(false);
    }
  };
 
  const handleRedirect = (url : string) => {
    window.open(url, "_blank");
  };

  // const handleVisualize = async () => {
  //   try {
  //     setVisualizing(true);
  //     setError("");
  //     setMessage("Preparing visualization...");
     
  //     // Call the backend to get visualization URL
  //     const response = await axios.get("http://localhost:8000/visualize-spec-graph/");
     
  //     if (response.data.visualization_url) {
  //       window.open(response.data.visualization_url, "_blank");
  //       setMessage("Visualization opened in new window.");
  //     } else {
  //       setMessage("Visualization ready!");
  //     }
     
  //     console.log(response.data);
  //   } catch (error: any) {
  //     setError(error?.response?.data?.detail || "Failed to visualize graph.");
  //     setMessage("");
  //     console.error(error);
  //   } finally {
  //     setVisualizing(false);
  //   }
  // };
 
  return (
    <div className={styles.card}>
      <h3 className="text-center font-medium">Specification Files Upload</h3>
      
      <div className={styles.inputGroup}>
        <label className={styles.label}>Specification Files (.pdf, .txt)</label>
        <input
          type="file"
          multiple
          accept=".pdf,.txt"
          onChange={(e) => {
            setSpecFiles(e.target.files);
            setError("");
          }}
          className={styles.inputField}
        />
        <small className={styles.hint}>
          Select one or more specification files to upload
        </small>
      </div>
      
      <div className={styles.buttonGroup}>
        <button
          onClick={handleUpload}
          className={styles.button}
          disabled={uploading || creating || !specFiles?.length}
        >
          {uploading ? "Uploading..." : "Upload Files"}
        </button>
       
        <button
          onClick={handleCreate}
          className={styles.button}
          disabled={uploading || creating }
        >
          {creating ? "Creating..." : "Create Graph"}
        </button>
       

        <button onClick={() => handleRedirect("http://localhost:3002/graphrag-visualizer",)}
          className={`${styles.button} ${!graphCreated ? styles.buttonDisabled : ''}`}>
              Visualiser le graphe de Contexte
          </button>
      </div>
      
      {message && <p className={styles.successMessage}>{message}</p>}
      {error && <p className={styles.errorMessage}>{error}</p>}
    </div>
  );
}