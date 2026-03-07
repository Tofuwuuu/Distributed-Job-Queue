import { useEffect, useState } from 'react'
import type { DashboardStats, Job, JobListResponse, Priority } from './api'
import { getStats, getJobs, submitJob } from './api'
import './App.css'

function formatDate(s: string | null) {
  if (!s) return '—'
  return new Date(s).toLocaleString()
}

function StatusBadge({ status }: { status: string }) {
  const c = status === 'completed' ? 'success' : status === 'processing' ? 'accent' : status === 'dlq' || status === 'failed' ? 'danger' : 'muted'
  return <span className={`badge badge-${c}`}>{status}</span>
}

function App() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [jobs, setJobs] = useState<JobListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<string>('')
  const [submitType, setSubmitType] = useState('echo')
  const [submitPayload, setSubmitPayload] = useState('{"message": "hello"}')
  const [submitPriority, setSubmitPriority] = useState<Priority>('normal')
  const [submitting, setSubmitting] = useState(false)

  const refresh = async () => {
    setError(null)
    try {
      const [s, j] = await Promise.all([
        getStats(),
        getJobs({ limit: 50, ...(filter ? { status: filter } : {}) }),
      ])
      setStats(s)
      setJobs(j)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
    const t = setInterval(refresh, 5000)
    return () => clearInterval(t)
  }, [filter])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      let payload: Record<string, unknown> = {}
      try {
        payload = JSON.parse(submitPayload || '{}')
      } catch {
        setError('Invalid JSON payload')
        return
      }
      await submitJob(submitType, payload, submitPriority)
      await refresh()
      setSubmitPayload('{}')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Submit failed')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading && !stats) {
    return (
      <div className="layout">
        <header className="header">
          <h1>Job Queue Dashboard</h1>
        </header>
        <p className="muted">Loading…</p>
      </div>
    )
  }

  return (
    <div className="layout">
      <header className="header">
        <h1>Job Queue Dashboard</h1>
        <p className="tagline">Monitor and submit jobs</p>
      </header>

      {error && <div className="banner error">{error}</div>}

      {stats && (
        <section className="stats">
          <div className="card">
            <span className="label">Pending</span>
            <span className="value">{stats.pending}</span>
          </div>
          <div className="card">
            <span className="label">Processing</span>
            <span className="value accent">{stats.processing}</span>
          </div>
          <div className="card">
            <span className="label">Completed</span>
            <span className="value success">{stats.completed}</span>
          </div>
          <div className="card">
            <span className="label">Failed</span>
            <span className="value">{stats.failed}</span>
          </div>
          <div className="card danger">
            <span className="label">DLQ</span>
            <span className="value">{stats.dlq}</span>
          </div>
          <div className="card queue-card">
            <span className="label">Queue lengths</span>
            <div className="queue-row">
              <span>High: {stats.queue_lengths.high}</span>
              <span>Normal: {stats.queue_lengths.normal}</span>
              <span>Low: {stats.queue_lengths.low}</span>
            </div>
          </div>
        </section>
      )}

      <section className="submit-section">
        <h2>Submit job</h2>
        <form onSubmit={handleSubmit} className="form">
          <div className="form-row">
            <label>Type</label>
            <select value={submitType} onChange={(e) => setSubmitType(e.target.value)}>
              <option value="echo">echo</option>
              <option value="sleep">sleep</option>
              <option value="random_fail">random_fail (test retry/DLQ)</option>
            </select>
          </div>
          <div className="form-row">
            <label>Priority</label>
            <select value={submitPriority} onChange={(e) => setSubmitPriority(e.target.value as Priority)}>
              <option value="high">high</option>
              <option value="normal">normal</option>
              <option value="low">low</option>
            </select>
          </div>
          <div className="form-row">
            <label>Payload (JSON)</label>
            <textarea value={submitPayload} onChange={(e) => setSubmitPayload(e.target.value)} rows={3} className="payload-input" />
          </div>
          <button type="submit" disabled={submitting}>{submitting ? 'Submitting…' : 'Submit'}</button>
        </form>
      </section>

      <section className="jobs-section">
        <div className="jobs-header">
          <h2>Jobs</h2>
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="">All</option>
            <option value="pending">pending</option>
            <option value="processing">processing</option>
            <option value="completed">completed</option>
            <option value="failed">failed</option>
            <option value="dlq">dlq</option>
          </select>
        </div>
        {jobs && (
          <div className="table-wrap">
            <table className="jobs-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>Retries</th>
                  <th>Created</th>
                  <th>Result / Error</th>
                </tr>
              </thead>
              <tbody>
                {jobs.jobs.map((j: Job) => (
                  <tr key={j.id}>
                    <td className="id-cell"><code>{j.id.slice(0, 8)}…</code></td>
                    <td>{j.job_type}</td>
                    <td><StatusBadge status={j.status} /></td>
                    <td>{j.priority}</td>
                    <td>{j.retries}/{j.max_retries}</td>
                    <td className="muted">{formatDate(j.created_at)}</td>
                    <td className="result-cell">
                      {j.result != null && <code>{JSON.stringify(j.result)}</code>}
                      {j.error_message && <span className="error-text">{j.error_message}</span>}
                      {!j.result && !j.error_message && '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {jobs && jobs.total > 0 && <p className="muted">Total: {jobs.total}</p>}
      </section>
    </div>
  )
}

export default App
