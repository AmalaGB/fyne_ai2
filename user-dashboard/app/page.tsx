"use client"; // This must be the very first line

import React, { useState } from 'react';

export default function Page() { // Must have 'export default'
  const [feedback, setFeedback] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rating: 5, review_text: feedback })
    });
    alert("Sent!");
  };

  return (
    <div className="p-8">
      <h1>Submit Feedback</h1>
      <textarea 
        onChange={(e) => setFeedback(e.target.value)}
        className="border p-2 block w-full text-black"
      />
      <button onClick={handleSubmit} className="bg-blue-500 text-white p-2 mt-2">
        Submit
      </button>
    </div>
  );
}