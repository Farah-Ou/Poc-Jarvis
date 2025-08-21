import React from "react";
import { useJira } from "./JiraContext";

export default function JiraProjectsList() {
  const { configs } = useJira();

  return (
    <div>
      <h2>Saved Jira Connections</h2>
      {configs.length === 0 ? (
        <p>No connections saved.</p>
      ) : (
        <ul>
          {configs.map((config, idx) => (
            <li key={idx}>
              <strong>{config.serverUrl}</strong> ({config.username})
              <ul>
                {config.projectKeys.map((key) => (
                  <li key={key}>{key}</li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
