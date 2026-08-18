import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

function Dashboard() {
  const navigate = useNavigate();
  const [topic, setTopic] = useState("");
  const [post, setPost] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [showHistory, setShowHistory] = useState(false);
  const [historyList, setHistoryList] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  async function fetchHistory() {
    setHistoryLoading(true);
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${import.meta.env.VITE_API_URL}/history`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setHistoryList(response.data.history || []);
    } catch (err) {
      console.log("Failed to fetch history", err);
    }
    setHistoryLoading(false);
  }

  function toggleHistory() {
    if (!showHistory) {
      fetchHistory();
    }
    setShowHistory(!showHistory);
  }

  async function generatePost() {
    if (!topic.trim()) {
      setError("Please enter a topic first.");
      return;
    }

    setLoading(true);
    setError("");
    setPost("");

    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/chat`,
        {
          raw_input: topic,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setPost(response.data.post);
      if (showHistory) {
        fetchHistory();
      }
    } catch (err) {
      console.log(err);
      setError("Something went wrong. Make sure the backend is running.");
    }

    setLoading(false);
  }

  function handleLogout() {
    localStorage.removeItem("token");
    navigate("/login");
  }

  function selectHistoryItem(item) {
    setTopic(item.topic);
    setPost(item.generated_post);
    setShowHistory(false);
  }

  return (
    <div className="container">
      <div className="header-row">
        <h1>LinkedIn Post Generator</h1>
        <div style={{ display: "flex", gap: "10px" }}>
          <button onClick={toggleHistory} className="history-btn">
            View History
          </button>
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </div>
      <p className="subtitle">Powered by LangGraph AI</p>

      <div className="input-section">
        <label htmlFor="topic-input">Enter your topic:</label>
        <input
          id="topic-input"
          type="text"
          placeholder="e.g. Artificial Intelligence, Remote Work..."
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && generatePost()}
        />

        <button onClick={generatePost} disabled={loading}>
          {loading ? "Generating..." : "Generate Post"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {post && (
        <div className="output-section">
          <h2>Generated LinkedIn Post:</h2>
          <div className="post-box">
            {post.split("\n").map((line, i) => (
              <p key={i}>{line}</p>
            ))}
          </div>
        </div>
      )}

      {/* Sidebar Overlay */}
      {showHistory && (
        <div className="sidebar-overlay" onClick={toggleHistory}>
          <div className="sidebar" onClick={(e) => e.stopPropagation()}>
            <div className="sidebar-header">
              <h2>Generation History</h2>
              <button className="close-btn" onClick={toggleHistory}>
                ✕
              </button>
            </div>
            <div className="sidebar-content">
              {historyLoading ? (
                <p>Loading history...</p>
              ) : historyList.length === 0 ? (
                <p>No past generations found.</p>
              ) : (
                historyList.map((item, index) => (
                  <div
                    key={index}
                    className="history-item"
                    onClick={() => selectHistoryItem(item)}
                  >
                    <strong>Topic: {item.topic}</strong>
                    <p className="history-preview">
                      {item.generated_post ? item.generated_post.substring(0, 90) + "..." : ""}
                    </p>
                    {item.created_at && (
                      <span className="history-date">
                        {new Date(item.created_at).toLocaleString()}
                      </span>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
