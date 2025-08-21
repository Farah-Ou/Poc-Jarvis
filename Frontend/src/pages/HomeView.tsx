// components/HomeView.tsx
import DataGraphSection from "../components/DataGraphSection";
import styles from "../styles/PageContainer.module.css";

export default function HomeView() {
  return (
    <>     
      <section className={styles.section}>
        <DataGraphSection />
      </section>
    </>
  );
}
