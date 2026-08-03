import { useEffect, useRef, useState } from 'react'
import { detectCategory, getCustomerInsight, strategyStreamUrl } from '../services/api'

export default function SlicePage() {
  const [idea, setIdea] = useState('')
  const [match, setMatch] = useState(null)
  const [agent, setAgent] = useState(null)
  const [strategy, setStrategy] = useState('')
  const [running, setRunning] = useState(false)
  const esRef = useRef(null)

  // live category preview, debounced 400ms
  useEffect(() => {
    if (idea.trim().length < 4) { setMatch(null); return }
    const t = setTimeout(() => detectCategory(idea).then(setMatch).catch(() => {}), 400)
    return () => clearTimeout(t)
  }, [idea])

  // close any open SSE stream on unmount — guards against a route change
  // mid-stream (Phase 4 adds routing) leaking the connection and burning quota
  useEffect(() => () => esRef.current?.close(), [])

  const analyze = async () => {
    setRunning(true); setAgent(null); setStrategy('')
    try {
      if (match?.category) {
        setAgent(await getCustomerInsight(match.category))
      }
      esRef.current?.close()
      const es = new EventSource(strategyStreamUrl(idea))
      esRef.current = es
      es.onmessage = (e) => setStrategy((s) => s + (JSON.parse(e.data).t ?? ''))
      es.addEventListener('done', () => { es.close(); setRunning(false) })
      es.onerror = () => { es.close(); setRunning(false) }
    } catch { setRunning(false) }
  }

  return (
    <div className="mx-auto max-w-2xl p-8 space-y-4">
      <h1 className="text-2xl font-bold">AI Business Strategy Advisor — slice</h1>
      <textarea
        className="w-full rounded border p-3"
        rows={3}
        placeholder="e.g. food delivery for hostel students"
        value={idea}
        onChange={(e) => setIdea(e.target.value)}
      />
      {match && (
        <p className="text-sm">
          {match.category
            ? `✓ Matched: ${match.category} (${Math.round(match.confidence * 100)}%)`
            : `No direct match — closest: ${match.closest}`}
        </p>
      )}
      <button
        onClick={analyze}
        disabled={running || idea.trim().length < 4}
        className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
      >
        {running ? 'Analyzing…' : 'Analyze'}
      </button>

      {agent && (
        <div className="rounded border p-4 text-sm">
          <p className="font-semibold">{agent.headline}</p>
          <p>{agent.insights.join(' · ')}</p>
          <p className="text-xs opacity-70">
            Source: {agent.source.dataset} ({agent.source.sample_size.toLocaleString()} reviews)
          </p>
        </div>
      )}
      {strategy && <div className="rounded border p-4 whitespace-pre-wrap">{strategy}</div>}
    </div>
  )
}
