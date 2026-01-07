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
        setRating(0);
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
    // This div centers everything on the screen
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      
      <div className="max-w-md w-full">
        <h1 className="text-3xl font-extrabold mb-8 text-center text-gray-900 tracking-tight">
          Customer Feedback
        </h1>
        
        <form onSubmit={handleSubmit} className="bg-white shadow-2xl rounded-3xl p-8 border border-gray-100 transition-all">
          
          {/* Requirement: Stars centered and yellow */}
          <div className="mb-10 text-center">
            <label className="block text-gray-500 text-sm font-semibold uppercase tracking-wider mb-4">
              Tap to Rate
            </label>
            <div className="flex justify-center items-center gap-3">
              {[1, 2, 3, 4, 5].map((num) => (
                <button
                  key={num}
                  type="button"
                  onClick={() => setRating(num)}
                  onMouseEnter={() => setHover(num)}
                  onMouseLeave={() => setHover(0)}
                  className="focus:outline-none transform transition-transform hover:scale-125 active:scale-95"
                >
                  <span className={`text-5xl leading-none transition-colors duration-200 
                    ${(hover || rating) >= num ? "text-yellow-400" : "text-gray-200"}
                    ${rating >= num ? "text-yellow-500" : ""} 
                  `}>
                    ★
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="mb-6">
            <textarea 
              required
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="What can we improve?..."
              className="w-full border-0 bg-gray-50 rounded-2xl p-5 text-gray-800 h-32 focus:ring-2 focus:ring-yellow-400 outline-none transition-all placeholder:text-gray-400"
            />
          </div>

          <button 
            type="submit"
            disabled={loading}
            className={`w-full py-4 rounded-2xl text-white font-bold text-lg transition-all shadow-xl active:scale-95 ${
              loading ? "bg-gray-300 cursor-not-allowed" : "bg-gray-900 hover:bg-black hover:shadow-2xl"
            }`}
          >
            {loading ? "Analyzing..." : "Submit Review"}
          </button>
        </form>

        {/* AI Success Feedback Section */}
        <div className="mt-8">
          {status === "success" && (
            <div className="bg-white border border-green-100 p-6 rounded-3xl shadow-lg animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <h3 className="text-green-900 font-bold">AI Assistant Says:</h3>
              </div>
              <p className="text-gray-700 leading-relaxed italic">
                "{aiResponse}"
              </p>
            </div>
          )}

          {status === "error" && (
            <div className="bg-red-50 text-red-700 p-4 rounded-2xl text-center font-medium">
              Connection error. Please try again.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}