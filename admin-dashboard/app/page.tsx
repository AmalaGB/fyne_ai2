'use client'
import { useEffect, useState } from 'react'

export default function AdminPanel() {
  const [data, setData] = useState<any[]>([]) // Initialize as empty array
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL;
    
    if (!backendUrl) {
      setError("Backend URL is not configured in Environment Variables.");
      setLoading(false);
      return;
    }

    fetch(`${backendUrl}/api/admin/list`)
      .then(res => {
        if (!res.ok) throw new Error(`Server Error: ${res.status}`);
        return res.json();
      })
      .then(result => {
        // SAFETY CHECK: Ensure the result is actually an array
        if (Array.isArray(result)) {
          setData(result);
        } else {
          console.error("Received non-array data:", result);
          setData([]);
        }
      })
      .catch(err => {
        console.error("Fetch error:", err);
        setError("Could not connect to backend. Make sure Render is live.");
      })
      .finally(() => setLoading(false));
  }, [])

  if (loading) return <div className="p-10 text-center text-gray-500">Connecting to AI Backend...</div>;
  if (error) return <div className="p-10 text-center text-red-500 font-bold">{error}</div>;

  return (
    <main className="p-10 bg-white min-h-screen text-black">
      <h1 className="text-3xl font-bold mb-6">Evaluation Results</h1>
      
      {data.length === 0 ? (
        <div className="p-10 border-2 border-dashed rounded text-center text-gray-400">
          No feedback entries found in the database.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse border border-gray-200">
            <thead className="bg-gray-100">
              <tr>
                <th className="border p-3 text-left">Rating</th>
                <th className="border p-3 text-left">Original Review</th>
                <th className="border p-3 text-left">AI Summary</th>
                <th className="border p-3 text-left">Recommended Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.map((item: any) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="border p-3 text-center font-bold">{item.rating}/5</td>
                  <td className="border p-3 text-sm">{item.review_text}</td>
                  <td className="border p-3 text-sm italic text-gray-700">
                    {item.ai_summary || "Processing..."}
                  </td>
                  <td className="border p-3">
                    <ul className="list-disc ml-4 text-xs space-y-1">
                      {Array.isArray(item.ai_actions) && item.ai_actions.length > 0 ? (
                        item.ai_actions.map((act: string, i: number) => (
                          <li key={i} className="text-blue-700">{act}</li>
                        ))
                      ) : (
                        <li className="text-gray-400 italic">No actions recommended</li>
                      )}
                    </ul>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  )
}
