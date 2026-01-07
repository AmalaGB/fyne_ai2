'use client'
import { useEffect, useState } from 'react'

export default function AdminPanel() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<string>("")

  const fetchData = async () => {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!backendUrl) return;

    try {
      const res = await fetch(`${backendUrl}/api/admin/list`);
      if (res.ok) {
        const result = await res.json();
        setData(result);
        setLastUpdated(new Date().toLocaleTimeString());
      }
    } catch (err) {
      console.error("Sync error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(); 
    const interval = setInterval(fetchData, 3000); // 3-second high-speed refresh
    return () => clearInterval(interval);
  }, []);

  const totalSubmissions = data.length;
  const avgRating = totalSubmissions > 0 
    ? (data.reduce((acc, curr) => acc + curr.rating, 0) / totalSubmissions).toFixed(1) 
    : 0;

  if (loading) return <div style={{ textAlign: 'center', padding: '50px', fontFamily: 'sans-serif' }}>Connecting to Live Feed...</div>;

  return (
    <main style={{ padding: '40px', backgroundColor: '#f9fafb', minHeight: '100vh', fontFamily: 'sans-serif', color: '#111827' }}>
      
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
          <h1 style={{ fontSize: '28px', fontWeight: 'bold', margin: 0 }}>Evaluation Results</h1>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', backgroundColor: '#fff', padding: '8px 15px', borderRadius: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
            <div style={{ width: '8px', height: '8px', backgroundColor: '#22c55e', borderRadius: '50%', boxShadow: '0 0 8px #22c55e' }}></div>
            <span style={{ fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>LIVE • Last sync: {lastUpdated}</span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '30px' }}>
          <div style={{ backgroundColor: 'white', padding: '25px', borderRadius: '20px', boxShadow: '0 4px 6px rgba(0,0,0,0.02)', border: '1px solid #f3f4f6' }}>
            {/* FIXED LINE 58: changed 'uppercase' to 'textTransform' */}
            <p style={{ color: '#9ca3af', margin: 0, fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase' }}>TOTAL ENTRIES</p>
            <h2 style={{ fontSize: '36px', margin: '10px 0 0 0' }}>{totalSubmissions}</h2>
          </div>
          <div style={{ backgroundColor: 'white', padding: '25px', borderRadius: '20px', boxShadow: '0 4px 6px rgba(0,0,0,0.02)', border: '1px solid #f3f4f6' }}>
            {/* FIXED LINE 62: changed 'uppercase' to 'textTransform' */}
            <p style={{ color: '#9ca3af', margin: 0, fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase' }}>AVG SATISFACTION</p>
            <h2 style={{ fontSize: '36px', margin: '10px 0 0 0', color: '#eab308' }}>{avgRating} <span style={{ fontSize: '20px' }}>/ 5</span></h2>
          </div>
        </div>

        <div style={{ backgroundColor: 'white', borderRadius: '24px', overflow: 'hidden', boxShadow: '0 20px 25px -5px rgba(13, 7, 7, 0.1)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #f1f5f9' }}>
              <tr>
                <th style={{ padding: '20px', fontSize: '13px', color: '#64748b' }}>RATING</th>
                <th style={{ padding: '20px', fontSize: '13px', color: '#64748b' }}>REVIEW</th>
                <th style={{ padding: '20px', fontSize: '13px', color: '#64748b' }}>AI ANALYSIS</th>
                <th style={{ padding: '20px', fontSize: '13px', color: '#64748b' }}>NEXT STEPS</th>
              </tr>
            </thead>
            <tbody>
              {data.map((item) => (
                <tr key={item.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '20px' }}>
                    <span style={{ backgroundColor: item.rating >= 4 ? '#fef9c3' : '#f1f5f9', color: '#a16207', padding: '6px 12px', borderRadius: '10px', fontWeight: 'bold' }}>
                      {item.rating} ★
                    </span>
                  </td>
                  <td style={{ padding: '20px', fontSize: '14px', color: '#334155', maxWidth: '250px' }}>{item.review_text}</td>
                  <td style={{ padding: '20px', fontSize: '14px', color: '#475569', lineHeight: '1.5' }}>
                    <div style={{ borderLeft: '3px solid #e2e8f0', paddingLeft: '12px' }}>{item.ai_summary}</div>
                  </td>
                  <td style={{ padding: '20px' }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {Array.isArray(item.ai_actions) && item.ai_actions.map((act: any, i: number) => (
                        <span key={i} style={{ backgroundColor: '#f0f9ff', color: '#0369a1', padding: '4px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '500', border: '1px solid #e0f2fe' }}>
                          {act}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.length === 0 && <div style={{ padding: '60px', textAlign: 'center', color: '#94a3b8' }}>Waiting for incoming reviews...</div>}
        </div>
      </div>
    </main>
  );
}