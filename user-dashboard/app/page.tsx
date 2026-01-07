"use client";

import React, { useState } from 'react';

export default function Page() {
  const [rating, setRating] = useState(0); // Start at 0 so no stars are "pre-chosen"
  const [hover, setHover] = useState(0);   // For a nice hover effect
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === 0) return alert("Please select a star rating!");
    
    setLoading(true);
    setStatus("idle");
    setAiResponse(null);

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
        setRating(0); // Reset after success
      } else {
        throw new Error("Failed");
      }
    } catch (err) {
      setStatus("error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto p-8 font-sans">
      <h1 className="text-3xl font-bold mb-6 text-center text-gray-800">Share Your Experience</h1>
      
      <form onSubmit={handleSubmit} className="bg-white shadow-2xl rounded-2xl p-8 border border-gray-100">
        {/* Requirement: Star Selection with "Deeper Color" logic */}
        <div className="mb-8 text-center">
          <label className="block text-gray-600 font-medium mb-3">How would you rate us?</label>
          <div className="flex justify-center gap-2">
            {[1, 2, 3, 4, 5].map((num) => (
              <button
                key={num}
                type="button"
                onClick={() => setRating(num)}
                onMouseEnter={() => setHover(num)}
                onMouseLeave={() => setHover(0)}
                className="text-4xl transition-all duration-150 transform hover:scale-110 focus:outline-none"
              >
                <span className={`
                  ${(hover || rating) >= num ? "text-yellow-500" : "text-gray-300"}
                  ${rating >= num ? "text-yellow-600 shadow-sm" : ""} 
                `}>
                  ★
                </span>
              </button>
            ))}
          </div>
          {rating > 0 && (
            <p className="text-sm mt-2 text-yellow-700 font-semibold">
              You selected {rating} {rating === 1 ? 'star' : 'stars'}
            </p>
          )}
        </div>

        <div className="mb-6">
          <label className="block text-gray-700 font-semibold mb-2">Detailed Review</label>
          <textarea 
            required
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="What did you like or dislike?"
            className="w-full border border-gray-200 rounded-xl p-4 text-black h-32 focus:ring-2 focus:ring-yellow-400 focus:border-transparent outline-none transition-all"
          />
        </div>

        <button 
          type="submit"
          disabled={loading}
          className={`w-full py-4 rounded-xl text-white font-bold text-lg transition-all shadow-lg ${
            loading ? "bg-gray-400 cursor-not-allowed" : "bg-black hover:bg-gray-800 active:transform active:scale-95"
          }`}
        >
          {loading ? "Analyzing with AI..." : "Submit Review"}
        </button>
      </form>

      {/* Success/Error Alerts */}
      <div className="mt-8 space-y-4">
        {status === "success" && (
          <div className="bg-yellow-50 border-l-4 border-yellow-500 p-6 rounded-xl shadow-md animate-fade-in">
            <h3 className="text-yellow-800 font-bold text-lg mb-2">Thank you! ✨</h3>
            <div className="bg-white p-4 rounded-lg border border-yellow-100 text-gray-700 italic">
              "{aiResponse}"
            </div>
          </div>
        )}

        {status === "error" && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-xl">
            <p className="text-red-700 font-medium">Something went wrong. Please check your connection.</p>
          </div>
        )}
      </div>
    </div>
  );
}