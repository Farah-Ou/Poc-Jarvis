// App.tsx
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import HeaderNav from "./components/HeaderNav";
import TcGenView from "./pages/TcGenView";
import HomeView from "./pages/HomeView";
import styles from "./styles/PageContainer.module.css";
import { JiraProvider } from "./components/JiraContext";
import { getOrCreateUserId } from "utils/userIDUtils";

export default function App() {
  const userId = getOrCreateUserId();

  return (
    <Router>
      <div className={styles.pageContainer}>
        <JiraProvider>
          <HeaderNav />
          <main className={styles.mainContent}>
            <Routes>
              <Route path="/" element={<HomeView />} />
              <Route path="/tcgen" element={<TcGenView />} />
            </Routes>
          </main>
        </JiraProvider>
      </div>
    </Router>
  );
}
