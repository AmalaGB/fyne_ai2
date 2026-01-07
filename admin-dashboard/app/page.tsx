'use client'
import { useEffect, useState } from 'react'

export default function AdminPanel() {
  const [data, setData] = useState([])

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/admin/list`)
      .then(res => res.json())
      .then(setData)
  }, [])

  return (
    <main className="p-10">
      <h1 className="text-3xl font-bold mb-6">Evaluation Results</h1>
      <table className="min-w-full border">
        <thead className="bg-gray-100">
          <tr>
            <th className="border p-2">Rating</th>
            <th className="border p-2">Original Review</th>
            <th className="border p-2">AI Summary</th>
            <th className="border p-2">Recommended Actions</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item: any) => (
            <tr key={item.id}>
              <td className="border p-2 text-center font-bold">{item.rating}/5</td>
              <td className="border p-2 text-sm">{item.review_text}</td>
              <td className="border p-2 text-sm italic">{item.ai_summary}</td>
              <td className="border p-2">
                <ul className="list-disc ml-4 text-xs">
                  {item.ai_actions?.map((act: string, i: number) => <li key={i}>{act}</li>)}
                </ul>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  )
}