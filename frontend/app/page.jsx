"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function buildMeter(score) {
  const total = 20;
  const filled = Math.round(score * total);
  return "▓".repeat(filled) + "░".repeat(total - filled);
}

function scanId() {
  return Math.random().toString(16).slice(2, 8).toUpperCase();
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [id, setId] = useState(scanId());

  async function checkUrl(e) {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      const data = await res.json();
      setResult(data);
      setId(scanId());
    } catch (err) {
      setError(
        `connection failed — is the backend running at ${API_URL}?`
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <div className="masthead">
        <h1 className="title">Phishing inspector</h1>
        <span className="scan-id">log #{id}</span>
      </div>

      <p className="subtitle">
       Paste a link. It'll tell you if it smells like phishing.
      </p>

      <form onSubmit={checkUrl}>
        <label className="field-label" htmlFor="url-input">
          URL to inspect
        </label>
        <div className="search-row">
          <input
            id="url-input"
            type="text"
            placeholder="http://paypal-secure-login.tk/verify"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <button type="submit" disabled={loading}>
            {loading ? "Scanning…" : "Scan"}
          </button>
        </div>
      </form>

      {error && <div className="error-text">error: {error}</div>}

      {result && (
        <div className="result">
          <div className="evidence-label">Submitted</div>
          <div className="evidence-url">{result.url}</div>

          <div className="verdict-row">
            <span className={`stamp ${result.risk_level}`}>
              {result.risk_level} risk
            </span>
            <div className="meter">
              <div className="meter-track">{buildMeter(result.risk_score)}</div>
              {Math.round(result.risk_score * 100)}% phishing probability
            </div>
          </div>

          <div className="findings-label">Findings</div>
          {result.top_signals.length === 0 ? (
            <div className="finding-clean">
              No structural red flags found in this URL.
            </div>
          ) : (
            result.top_signals.map((s, i) => (
              <div className="finding-item" key={i}>
                <span className="finding-marker">▸</span>
                <span>{s}</span>
              </div>
            ))
          )}
        </div>
      )}

      <div className="footnote">
        This reads the URL string only and never visits the link. It's a
        portfolio project, not production security software so don't treat
        it as your only line of defense.
      </div>
    </main>
  );
}