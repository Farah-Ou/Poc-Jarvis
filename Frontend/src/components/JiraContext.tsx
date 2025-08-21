// src/context/JiraContext.tsx
import React, {
  createContext,
  useState,
  useContext,
  ReactNode,
  useEffect,
} from "react";

// Define types
type JiraConfig = {
  serverUrl: string;
  username: string;
  projectKeys: string[]; // One config can have multiple project keys
};

type JiraContextType = {
  configs: JiraConfig[];
  addOrUpdateConfig: (
    serverUrl: string,
    username: string,
    projectKey: string | null
  ) => void;
  removeConfig: (serverUrl: string) => void;
  getConnection: (serverUrl: string) => JiraConfig | undefined;
};

// Create context
const JiraContext = createContext<JiraContextType | undefined>(undefined);

// Provider component
export function JiraProvider({ children }: { children: ReactNode }) {
  const [configs, setConfigs] = useState<JiraConfig[]>(() => {
    // Load from localStorage
    const saved = localStorage.getItem("jiraConfigs");
    return saved ? JSON.parse(saved) : [];
  });

  // Save to localStorage whenever configs change
  useEffect(() => {
    localStorage.setItem("jiraConfigs", JSON.stringify(configs));
  }, [configs]);

  const addOrUpdateConfig = (
    serverUrl: string,
    username: string,
    projectKey: string | null
  ) => {
    const normalizedUrl = serverUrl.trim().toLowerCase();
    const normalizedKey = projectKey ? projectKey.trim().toUpperCase() : null;

    setConfigs((prev) => {
      const existingIndex = prev.findIndex(
        (c) => c.serverUrl.toLowerCase() === normalizedUrl
      );

      if (existingIndex > -1) {
        const updated = [...prev];
        const config = updated[existingIndex];

        if (projectKey && !config.projectKeys.includes(normalizedKey!)) {
          updated[existingIndex] = {
            ...config,
            username,
            projectKeys: [...config.projectKeys, normalizedKey!],
          };
        } else {
          updated[existingIndex] = { ...config, username };
        }
        return updated;
      } else {
        return [
          ...prev,
          {
            serverUrl,
            username,
            projectKeys: projectKey ? [normalizedKey!] : [],
          },
        ];
      }
    });
  };

  const removeConfig = (serverUrl: string) => {
    setConfigs((prev) =>
      prev.filter((c) => c.serverUrl.toLowerCase() !== serverUrl.toLowerCase())
    );
  };

  const getConnection = (serverUrl: string) => {
    return configs.find(
      (c) => c.serverUrl.toLowerCase() === serverUrl.toLowerCase()
    );
  };

  return (
    <JiraContext.Provider
      value={{ configs, addOrUpdateConfig, removeConfig, getConnection }}
    >
      {children}
    </JiraContext.Provider>
  );
}

// Custom hook for easy usage
export function useJira() {
  const context = useContext(JiraContext);
  if (!context) {
    throw new Error("useJira must be used within JiraProvider");
  }
  return context;
}
