
import styles from '../styles/DataGraphSection.module.css';
import UserStoriesForm from "./UserStoriesForm";
import CombinedFileUploadForm from "./CombinedFileUploadForm";
import TCHistoryForm from "./TCHistoryForm";

export default function DataGraphSection() {
  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Create Visual graph databases with your data</h2>
      <div className={styles.graphSection}>
        <UserStoriesForm />
        
        <CombinedFileUploadForm />
       
        <TCHistoryForm />
      </div>
    </div>
  );
}