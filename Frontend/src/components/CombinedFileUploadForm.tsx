import { useState } from "react";
import axios from "axios";
import styles from "../styles/BusinessDomainForm.module.css";
import { useJira } from "./JiraContext"; // Ensure correct path
import { getOrCreateUserId } from "utils/userIDUtils";

interface UploadResults {
  specifications?: {
    saved_files: string[];
    errors: string[];
    total: number;
    successful: number;
  };
  business_domain?: {
    saved_files: string[];
    errors: string[];
    total: number;
    successful: number;
  };
  company_guidelines?: {
    saved_files: string[];
    errors: string[];
    total: number;
    successful: number;
  };
}

interface UploadResponse {
  status: string;
  message: string;
  results: UploadResults;
  summary: {
    total_files: number;
    total_successful: number;
    total_failed: number;
    categories_processed: number;
  };
}

export default function CombinedFileUploadForm() {
  const [jiraProjectKey, setJiraProjectKey] = useState(""); // ✅ Required first
  const [specFiles, setSpecFiles] = useState<FileList | null>(null);
  const [businessFiles, setBusinessFiles] = useState<FileList | null>(null);
  const [guidelinesFiles, setGuidelinesFiles] = useState<FileList | null>(null);
  const [uploading, setUploading] = useState(false);
  const [creatingSpec, setCreatingSpec] = useState(false);
  const [creatingGuidelines, setCreatingGuidelines] = useState(false);
  const [creatingBusinessExpert, setCreatingBusinessExpert] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [uploadResults, setUploadResults] = useState<UploadResults | null>(
    null
  );
  const [specGraphCreated, setSpecGraphCreated] = useState(false);
  const [guidelinesGraphCreated, setGuidelinesGraphCreated] = useState(false);
  const [businessExpertGraphCreated, setBusinessExpertGraphCreated] =
    useState(false);

  // ✅ Get Jira project keys from context
  const { configs } = useJira();
  const allProjectKeys = Array.from(
    new Set(configs.flatMap((config) => config.projectKeys))
  ).sort();

  const handleUpload = async () => {
    if (!jiraProjectKey) {
      setError("Please select a Jira project first.");
      return;
    }

    if (!specFiles && !businessFiles && !guidelinesFiles) {
      setError("Please select at least one file to upload.");
      return;
    }

    const formData = new FormData();
    formData.append("jira_project_key", jiraProjectKey);
    formData.append("user_id", getOrCreateUserId());

    // Add spec files
    if (specFiles) {
      for (const file of Array.from(specFiles)) {
        formData.append("spec_files", file);
      }
    }

    // Add business domain files
    if (businessFiles) {
      for (const file of Array.from(businessFiles)) {
        formData.append("business_domain_files", file);
      }
    }

    // Add company guidelines files
    if (guidelinesFiles) {
      for (const file of Array.from(guidelinesFiles)) {
        formData.append("company_guidelines_files", file);
      }
    }

    try {
      setUploading(true);
      setError("");
      setMessage("Uploading files...");

      const response = await axios.post<UploadResponse>(
        "http://localhost:8000/api/files/documents/upload",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );

      setUploadResults(response.data.results);
      setMessage(response.data.message);
      console.log("Upload response:", response.data);
    } catch (error: any) {
      setError(
        error?.response?.data?.detail || "Upload failed. Please try again."
      );
      setMessage("");
      console.error("Upload error:", error);
    } finally {
      setUploading(false);
    }
  };

  const handleCreateSpecGraph = async () => {
    try {
      setCreatingSpec(true);
      setError("");
      setMessage("Creating specification graph... This may take a moment.");

      const response = await axios.post(
        `http://localhost:8000/api/graphs/spec/create/${jiraProjectKey}`
      );

      setMessage("Specification graph created successfully!");
      setSpecGraphCreated(true);
      console.log("Spec graph response:", response.data);
    } catch (error: any) {
      setError(
        error?.response?.data?.detail || "Failed to create specification graph."
      );
      setMessage("");
      console.error("Spec graph error:", error);
    } finally {
      setCreatingSpec(false);
    }
  };

  const handleCreateGuidelinesGraph = async () => {
    try {
      setCreatingGuidelines(true);
      setError("");
      setMessage("Creating guidelines graph... This may take a moment.");

      const response = await axios.post(
        `http://localhost:8000/api/graphs/guidelines/create/${jiraProjectKey}`
      );

      setMessage("Guidelines graph created successfully!");
      setGuidelinesGraphCreated(true);
      console.log("Guidelines graph response:", response.data);
    } catch (error: any) {
      setError(
        error?.response?.data?.detail || "Failed to create guidelines graph."
      );
      setMessage("");
      console.error("Guidelines graph error:", error);
    } finally {
      setCreatingGuidelines(false);
    }
  };

  const handleCreateBusinessExpertGraph = async () => {
    try {
      setCreatingBusinessExpert(true);
      setError("");
      setMessage("Creating business expert graph... This may take a moment.");

      const response = await axios.post(
        `http://localhost:8000/api/graphs/Business-Domain/create/${jiraProjectKey}`
      );

      setMessage("Business expert graph created successfully!");
      setBusinessExpertGraphCreated(true);
      console.log("Business expert graph response:", response.data);
    } catch (error: any) {
      setError(
        error?.response?.data?.detail ||
          "Failed to create business expert graph."
      );
      setMessage("");
      console.error("Business expert graph error:", error);
    } finally {
      setCreatingBusinessExpert(false);
    }
  };

  const handleRedirect = (url: string) => {
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const getFileCount = (files: FileList | null) => {
    return files ? files.length : 0;
  };

  const getTotalFiles = () => {
    return (
      getFileCount(specFiles) +
      getFileCount(businessFiles) +
      getFileCount(guidelinesFiles)
    );
  };

  const renderUploadSummary = () => {
    if (!uploadResults) return null;

    return (
      <div className={styles.uploadSummary}>
        <h4>Upload Summary:</h4>
        {uploadResults.specifications && (
          <div className={styles.categoryResult}>
            <strong>Specifications:</strong>{" "}
            {uploadResults.specifications.successful}/
            {uploadResults.specifications.total} files uploaded
            {Array.isArray(uploadResults.specifications.errors) &&
              uploadResults.specifications.errors.length > 0 && (
                <div className={styles.errorList}>
                  Errors: {uploadResults.specifications.errors.join(", ")}
                </div>
              )}
          </div>
        )}
        {uploadResults.business_domain && (
          <div className={styles.categoryResult}>
            <strong>Business Domain:</strong>{" "}
            {uploadResults.business_domain.successful}/
            {uploadResults.business_domain.total} files uploaded
            {Array.isArray(uploadResults.business_domain.errors) &&
              uploadResults.business_domain.errors.length > 0 && (
                <div className={styles.errorList}>
                  Errors: {uploadResults.business_domain.errors.join(", ")}
                </div>
              )}
          </div>
        )}
        {uploadResults.company_guidelines && (
          <div className={styles.categoryResult}>
            <strong>Company Guidelines:</strong>{" "}
            {uploadResults.company_guidelines.successful}/
            {uploadResults.company_guidelines.total} files uploaded
            {Array.isArray(uploadResults.company_guidelines.errors) &&
              uploadResults.company_guidelines.errors.length > 0 && (
                <div className={styles.errorList}>
                  Errors: {uploadResults.company_guidelines.errors.join(", ")}
                </div>
              )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={styles.card}>
      <h3 className="text-center font-medium">
        Chargement de fichiers & Création de graphes
      </h3>

      {/* ✅ 1. REQUIRED: Jira Project Key (First!) */}
      <div className={styles.inputGroup}>
        <label className={styles.label}>
          Sélectionner le projet Jira <span style={{ color: "red" }}>*</span>
        </label>

        {allProjectKeys.length > 0 ? (
          <select
            value={jiraProjectKey}
            onChange={(e) => {
              setJiraProjectKey(e.target.value);
              setMessage("");
              setError("");
            }}
            className={styles.inputField}
          >
            <option value="">-- Choisir un projet Jira --</option>
            {allProjectKeys.map((key) => (
              <option key={key} value={key}>
                {key}
              </option>
            ))}
          </select>
        ) : (
          <p className={styles.hint}>
            ⚠️ Aucun projet Jira enregistré. Veuillez aller dans les{" "}
            <strong>Paramètres</strong> pour connecter.
          </p>
        )}
      </div>

      {/* ❗ Show file uploads only if project is selected */}
      {jiraProjectKey ? (
        <>
          {/* Specification Files */}
          <div className={styles.inputGroup}>
            <label className={styles.label}>
              Votre Agent Product Owner !
              {/* <br></br> Fichiers de Spécification (.pdf, .txt) */}
              {getFileCount(specFiles) > 0 && (
                <span className={styles.fileCount}>
                  {" "}
                  ({getFileCount(specFiles)} selected)
                </span>
              )}
            </label>
            <label className={styles.fileUpload}>
              📂 Choisir Fichiers de Spécification
              <input
                type="file"
                accept=".pdf,.txt"
                multiple
                onChange={(e) => setSpecFiles(e.target.files)}
                style={{ display: "none" }}
              />
            </label>
          </div>

          {/* Business Domain Files */}
          <div className={styles.inputGroup}>
            <label className={styles.label}>
              Votre Agent Expert Métier personnalisé !
              {/* <br></br> Fichiers Domaine métier (.pdf, .txt)  */}
              {getFileCount(businessFiles) > 0 && (
                <span className={styles.fileCount}>
                  {" "}
                  ({getFileCount(businessFiles)} selected)
                </span>
              )}
            </label>
            <label className={styles.fileUpload}>
              📂 Choisir Fichiers Domaine métier
              <input
                type="file"
                accept=".pdf,.txt"
                multiple
                onChange={(e) => setBusinessFiles(e.target.files)}
                style={{ display: "none" }}
              />
            </label>
          </div>

          {/* Company Guidelines Files */}
          <div className={styles.inputGroup}>
            <label className={styles.label}>
              Votre Agent Consultant Réglementation Interne !
              {/* <br></br> Fichiers normatifs (.pdf, .txt) */}
              {getFileCount(guidelinesFiles) > 0 && (
                <span className={styles.fileCount}>
                  {" "}
                  ({getFileCount(guidelinesFiles)} selected)
                </span>
              )}
            </label>
            <label className={styles.fileUpload}>
              📂 Choisir Fichiers normatifs internes
              <input
                type="file"
                accept=".pdf,.txt"
                multiple
                onChange={(e) => setGuidelinesFiles(e.target.files)}
                style={{ display: "none" }}
              />
            </label>
          </div>

          {/* Upload Button */}
          <div className={styles.buttonGroup}>
            <button
              onClick={handleUpload}
              className={styles.uploadButton}
              disabled={uploading || getTotalFiles() === 0}
            >
              {uploading
                ? "Uploading..."
                : `Upload Files (${getTotalFiles()} selected)`}
            </button>
          </div>

          {/* Upload Summary */}
          {renderUploadSummary()}
        </>
      ) : (
        <p className={styles.hint}>
          Veuillez sélectionner un projet Jira pour activer les chargements de
          fichiers.
        </p>
      )}

      {/* Graph Creation Buttons (disabled until graph is uploaded/created) */}
      <div className={styles.buttonGroup}>
        <button
          onClick={handleCreateSpecGraph}
          className={styles.button}
          disabled={!jiraProjectKey || creatingSpec}
        >
          {creatingSpec ? "Creating..." : "Créer Graphe SPEC"}
        </button>

        <button
          onClick={handleCreateGuidelinesGraph}
          className={styles.button}
          disabled={!jiraProjectKey || creatingGuidelines}
        >
          {creatingGuidelines ? "Creating..." : "Créer Graphe Normes"}
        </button>

        <button
          onClick={handleCreateBusinessExpertGraph}
          className={styles.button}
          disabled={!jiraProjectKey || creatingBusinessExpert}
        >
          {creatingBusinessExpert ? "Creating..." : "Créer Graphe Métier"}
        </button>
      </div>

      {/* Visualization Buttons */}
      <div className={styles.buttonGroup}>
        <button
          onClick={() =>
            handleRedirect(
              `http://localhost:3001/graphrag-visualizer#/graph?projectId=${jiraProjectKey}&graphId=spec_graph`
            )
          }
          className={styles.button}
          disabled={!specGraphCreated}
        >
          Visualiser Graphe SPEC
        </button>
        <button
          onClick={() =>
            handleRedirect(
              `http://localhost:3001/graphrag-visualizer#/graph?projectId=${jiraProjectKey}&graphId=guideline_graph`
            )
          }
          className={styles.button}
          disabled={!guidelinesGraphCreated}
        >
          Visualiser Graphe Normes
        </button>

        <button
          onClick={() =>
            handleRedirect(
              `http://localhost:3001/graphrag-visualizer#/graph?projectId=${jiraProjectKey}&graphId=business_domain_graph`
            )
          }
          className={styles.button}
          disabled={!businessExpertGraphCreated}
        >
          Visualiser Graphe Métier
        </button>
      </div>

      {/* Messages */}
      {message && <p className={styles.successMessage}>{message}</p>}
      {error && <p className={styles.errorMessage}>{error}</p>}
    </div>
  );
}
