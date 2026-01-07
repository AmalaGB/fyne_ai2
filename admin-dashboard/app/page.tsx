'use client'
import { useEffect, useState } from 'react'

export default function AdminPanel() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Auto-refresh function
  const fetchData = async () => {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!backendUrl) return;

    try {
      const res = await fetch(`${backendUrl}/api/admin/list`);
      if (!res.ok) throw new Error(`Server Error: ${res.status}`);
      const result = await res.json();
      if (Array.isArray(result)) {
        setData(result);
      }
    } catch (err) {
      console.error("Fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(); // Initial fetch

    // REQUIREMENT: Auto-refreshing list (every 10 seconds)
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  // Analytics Logic: Calculate Rating Counts
  const totalSubmissions = data.length;
  const avgRating = totalSubmissions > 0 
    ? (data.reduce((acc, curr) => acc + curr.rating, 0) / totalSubmissions).toFixed(1) 
    : 0;

  if (loading) return <div style={{ textAlign: 'center', padding: '50px', color: '#6b7280' }}>Loading Admin Data...</div>;
  if (error) return <div style={{ textAlign: 'center', padding: '50px', color: '#ef4444' }}>{error}</div>;

  return (
    <main style={{ padding: '40px', backgroundColor: '#f3f4f6', minHeight: '100vh', fontFamily: 'sans-serif', color: '#111827' }}>
      
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '30px' }}>Admin Evaluation Dashboard</h1>

        {/* ANALYTICS SECTION */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '30px' }}>
          <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '15px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)' }}>
            <p style={{ color: '#6b7280', margin: 0, fontSize: '14px' }}>Total Reviews</p>
            <h2 style={{ fontSize: '28px', margin: '5px 0 0 0' }}>{totalSubmissions}</h2>
          </div>
          <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '15px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)' }}>
            <p style={{ color: '#6b7280', margin: 0, fontSize: '14px' }}>Average Rating</p>
            <h2 style={{ fontSize: '28px', margin: '5px 0 0 0', color: '#fbbf24' }}>★ {avgRating}</h2>
          </div>
        </div>

        {/* FEEDBACK LIST */}
        <div style={{ backgroundColor: 'white', borderRadius: '20px', overflow: 'hidden', boxShadow: '0 10px 15px rgba(0,0,0,0.1)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ backgroundColor: '#111827', color: 'white' }}>
              <tr>
                <th style={{ padding: '15px', textAlign: 'left' }}>Rating</th>
                <th style={{ padding: '15px', textAlign: 'left' }}>User Review</th>
                <th style={{ padding: '15px', textAlign: 'left' }}>AI Summary</th>
                <th style={{ padding: '15px', textAlign: 'left' }}>Recommended Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.map((item) => (
                <tr key={item.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                  <td style={{ padding: '15px', fontWeight: 'bold', color: '#fbbf24', fontSize: '18px' }}>
                    {item.rating} ★
                  </td>
                  <td style={{ padding: '15px', fontSize: '14px', maxWidth: '300px' }}>
                    {item.review_text}
                  </td>
                  <td style={{ padding: '15px', fontSize: '14px', fontStyle: 'italic', color: '#4b5563' }}>
                    {item.ai_summary}
                  </td>
                  <td style={{ padding: '15px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                      {Array.isArray(item.ai_actions) && item.ai_actions.map((act: any, i: number) => (
                        <span key={i} style={{ backgroundColor: '#eff6ff', color: '#1d4ed8', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', width: 'fit-content' }}>
                          • {act}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.length === 0 && (
            <div style={{ padding: '40px', textAlign: 'center', color: '#9ca3af' }}>No submissions found yet.</div>
          )}
        </div>
      </div>
    </main>
  );
}