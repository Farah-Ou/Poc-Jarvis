

import { useState } from "react";
import styles from "../styles/TestFormatSelector.module.css";
import { getOrCreateUserId } from "utils/userIDUtils";

export default function TestFormatSelector() {
  const [selectedFormat, setSelectedFormat] = useState<string | null>(null);
  const [responseMsg, setResponseMsg] = useState<string | null>(null);

  const handleFormatSelect = (format: string) => {
    setSelectedFormat(format);
    setResponseMsg(null); // clear any previous message
  };

  const handleSubmit = async () => {
    if (!selectedFormat) {
      setResponseMsg("Veuillez sélectionner un format avant de confirmer.");
      return;
    }

    try { 
      const response = await fetch("http://localhost:8003/files/selected-format/upload", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ format: selectedFormat, user_id:getOrCreateUserId() })
      });

      if (!response.ok) {
        throw new Error("Échec de l'envoi au backend.");
      }

      const result = await response.json();
      setResponseMsg("Format envoyé avec succès !");
    } catch (error) {
      console.error(error);
      setResponseMsg("Erreur lors de l'envoi au backend.");
    }
  };

  return (
    <div className={styles.formSection}>
      <h2>Format des cas de Test</h2>
      <div className={styles.formatOptions}>
        {/* Format cards as before */}
        {[...Array(3)].map((_, i) => {
          const formats = [
            {
              label: "Gherkin sans paramètres",
              content: (
                <>
                  GIVEN je suis sur la page de login<br />
                  WHEN j'introduis mon adresse email<br />
                  AND j'introduis mon mot de passe<br />
                  THEN je vois un message de succès d'authentification<br />
                  AND je suis déplacé vers la page Home.
                </>
              )
            },
            {
              label: "Gherkin avec paramètres",
              content: (
                <>
                  GIVEN le JDD à utiliser est un utilisateur<br />
                  AND la valeur pour email est {"<email>"}<br />
                  AND la valeur pour mot de passe est {"<mdp>"}<br />
                  WHEN je clique sur se connecter<br />
                  THEN je vois un message {"<msg_authentic>"}<br />
                  AND le code retour est {"<code>"}
                </>
              )
            },
            {
              label: "Format en steps language naturel",
              content: (
                <>
                  1- Je suis sur la page de login<br />
                  2- J'introduis mon adresse email<br />
                  3- J'introduis mon mot de passe<br />
                  4- Je vois un message de succès d'authentification<br />
                  5- Je suis déplacé vers la page Home.
                </>
              )
            }
          ];

          const { label, content } = formats[i];
          return (
            <div key={i} className={styles.formatOption}>
              <p>
                <strong>{label}</strong><br />
                {content}
              </p>
              <div className={styles.buttonContainer}>
                <button onClick={() => handleFormatSelect(label)}>
                  Selectionner Format {i + 1}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {selectedFormat && <p className={styles.selectedFormat}>Format sélectionné : {selectedFormat}</p>}

      <div className={styles.buttonContainer}>
        <button className={styles.confirmButton} onClick={handleSubmit}>
        Confirmer
        </button>
      </div>

      {responseMsg && <p className={styles.selectedFormat}>{responseMsg}</p>}
    </div>
  );
}
