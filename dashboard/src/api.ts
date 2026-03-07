const API = '/api';

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'dlq';
export type Priority = 'high' | 'normal' | 'low';

export interface Job {
  id: string;
  job_type: string;
  payload: Record<string, unknown>;
  status: JobStatus;
  priority: string;
  retries: number;
  max_retries: number;
  result: Record<string, unknown> | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface DashboardStats {
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  dlq: number;
  queue_lengths: {
    high: number;
    normal: number;
    low: number;
    dlq: number;
  };
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
}

export async function getStats(): Promise<DashboardStats> {
  const r = await fetch(`${API}/jobs/stats`);
  if (!r.ok) throw new Error('Failed to fetch stats');
  return r.json();
}

export async function getJobs(params?: { status?: string; job_type?: string; limit?: number; offset?: number }): Promise<JobListResponse> {
  const search = new URLSearchParams();
  if (params?.status) search.set('status', params.status);
  if (params?.job_type) search.set('job_type', params.job_type);
  if (params?.limit) search.set('limit', String(params.limit));
  if (params?.offset) search.set('offset', String(params.offset));
  const r = await fetch(`${API}/jobs?${search}`);
  if (!r.ok) throw new Error('Failed to fetch jobs');
  return r.json();
}

export async function getJob(id: string): Promise<Job> {
  const r = await fetch(`${API}/jobs/${id}`);
  if (!r.ok) throw new Error('Failed to fetch job');
  return r.json();
}

export async function submitJob(job_type: string, payload: Record<string, unknown>, priority: Priority): Promise<Job> {
  const r = await fetch(`${API}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_type, payload, priority }),
  });
  if (!r.ok) throw new Error('Failed to submit job');
  return r.json();
}
