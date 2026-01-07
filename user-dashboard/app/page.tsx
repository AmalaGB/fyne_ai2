"use client";

import React, { useState } from 'react';

export default function Page() {
  const [rating, setRating] = useState(0);
  const [hover, setHover] = useState(0);
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === 0) return alert("Please select a star rating!");
    setLoading(true);
    setStatus("idle");

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating, review_text: feedback })
      });
      const data = await response.json();
      if (response.ok) {
        setStatus("success");
        setAiResponse(data.ai_user_response);
        setFeedback(""); 
        setRating(0);
      } else { throw new Error(); }
    } catch (err) {
      setStatus("error");
    } finally { setLoading(false); }
  };

  return (
    /* Force Center using Inline Styles */
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column',
      alignItems: 'center', 
      justifyContent: 'center', 
      minHeight: '100vh', 
      backgroundColor: '#f9fafb',
      padding: '20px',
      fontFamily: 'sans-serif'
    }}>
      
      <div style={{ maxWidth: '400px', width: '100%' }}>
        <h1 style={{ textAlign: 'center', color: '#111827', marginBottom: '2rem', fontSize: '28px', fontWeight: 'bold' }}>
          Customer Feedback
        </h1>
        
        <form onSubmit={handleSubmit} style={{ backgroundColor: 'white', padding: '30px', borderRadius: '20px', boxShadow: '0 10px 25px rgba(0,0,0,0.1)' }}>
          
          <div style={{ textAlign: 'center', marginBottom: '30px' }}>
            <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '15px', fontWeight: '600' }}>TAP A STAR TO RATE</p>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '10px' }}>
              {[1, 2, 3, 4, 5].map((num) => (
                <button
                  key={num}
                  type="button"
                  onClick={() => setRating(num)}
                  onMouseEnter={() => setHover(num)}
                  onMouseLeave={() => setHover(0)}
                  style={{ 
                    background: 'none', 
                    border: 'none', 
                    cursor: 'pointer', 
                    fontSize: '45px',
                    outline: 'none',
                    /* FORCE YELLOW COLOR */
                    color: (hover || rating) >= num ? '#fbbf24' : '#e5e7eb',
                    transition: 'color 0.2s'
                  }}
                >
                  ★
                </button>
              ))}
            </div>
          </div>

          <textarea 
            required
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Tell us more..."
            style={{ 
              width: '100%', 
              border: '1px solid #e5e7eb', 
              borderRadius: '12px', 
              padding: '15px', 
              height: '120px', 
              marginBottom: '20px',
              fontSize: '16px',
              boxSizing: 'border-box'
            }}
          />

          <button 
            type="submit"
            disabled={loading}
            style={{ 
              width: '100%', 
              padding: '15px', 
              borderRadius: '12px', 
              backgroundColor: loading ? '#d1d5db' : '#000000', 
              color: 'white', 
              fontWeight: 'bold', 
              fontSize: '16px',
              border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? "Processing..." : "Submit Review"}
          </button>
        </form>

        {status === "success" && (
          <div style={{ marginTop: '25px', padding: '20px', backgroundColor: '#ecfdf5', borderRadius: '15px', borderLeft: '5px solid #10b981' }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#065f46' }}>AI Response:</h4>
            <p style={{ margin: 0, color: '#374151', fontStyle: 'italic' }}>"{aiResponse}"</p>
          </div>
        )}
      </div>
    </div>
  );
}