"use client";

import React, { useState } from 'react';

export default function Page() {
  const [rating, setRating] = useState(5);
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
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
        setAiResponse(data.ai_user_response); // Show the response from FastAPI
        setFeedback(""); // Clear text area on success
      } else {
        throw new Error("Failed to submit");
      }
    } catch (err) {
      setStatus("error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto p-8 font-sans">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Customer Feedback</h1>
      
      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6 border border-gray-100">
        {/* Requirement: Select a star rating (1–5) */}
        <div className="mb-4">
          <label className="block text-gray-700 font-semibold mb-2">Rating</label>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((num) => (
              <button
                key={num}
                type="button"
                onClick={() => setRating(num)}
                className={`w-10 h-10 rounded-full border ${
                  rating >= num ? "bg-yellow-400 border-yellow-500 text-white" : "bg-gray-100 text-gray-400"
                } transition-colors font-bold`}
              >
                {num}
              </button>
            ))}
          </div>
        </div>

        {/* Requirement: Write a short review */}
        <div className="mb-4">
          <label className="block text-gray-700 font-semibold mb-2">Your Review</label>
          <textarea 
            required
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Tell us what you think..."
            className="w-full border border-gray-300 rounded-md p-3 text-black h-32 focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>

        {/* Requirement: Submit the review & show loading/success state */}
        <button 
          type="submit"
          disabled={loading}
          className={`w-full py-3 rounded-md text-white font-bold transition-all ${
            loading ? "bg-gray-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {loading ? "Processing with AI..." : "Submit Feedback"}
        </button>
      </form>

      {/* Requirement: Show clear success / error state */}
      <div className="mt-6">
        {status === "success" && (
          <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded shadow-sm">
            <h3 className="text-green-800 font-bold mb-1">Feedback Sent Successfully!</h3>
            {/* Requirement: AI-generated response must be shown */}
            <p className="text-gray-700 italic">" {aiResponse} "</p>
          </div>
        )}

        {status === "error" && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
            <p className="text-red-700 font-semibold">Error: Could not connect to the server. Please try again.</p>
          </div>
        )}
      </div>
    </div>
  );
}