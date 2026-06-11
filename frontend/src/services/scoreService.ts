import { mockGetScore } from '../mocks/score'
import type { ApiResponse } from '../types/api'
import type { ScoreData, ScoreInstrument, VocalVersion } from '../types/score'
import api, { rethrowApiError, useScoreMock } from './api'

export interface ScoreJobSnapshot {
  job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  stage: string
  stage_label: string
  error_code?: string | null
  error_message?: string | null
  result?: ScoreData | null
}

export async function getScore(
  neteaseSongId: number,
  instrument: ScoreInstrument,
  vocalVersion: VocalVersion = 'male',
): Promise<ScoreData> {
  if (useScoreMock) {
    const res = mockGetScore(neteaseSongId, instrument)
    if (res.code !== 200 || !res.data) throw new Error(res.message)
    return res.data
  }

  try {
    const { data } = await api.get<ApiResponse<ScoreData>>(`/v1/songs/${neteaseSongId}/score`, {
      params: { instrument, vocal_version: vocalVersion },
    })
    if (data.code !== 200 || !data.data) throw new Error(data.message)
    return data.data
  } catch (err) {
    rethrowApiError(err)
  }
}

export async function startScoreJob(
  neteaseSongId: number,
  instrument: ScoreInstrument,
  vocalVersion: VocalVersion = 'male',
): Promise<ScoreJobSnapshot> {
  const { data } = await api.post<ApiResponse<ScoreJobSnapshot>>(
    `/v1/songs/${neteaseSongId}/score/jobs`,
    null,
    { params: { instrument, vocal_version: vocalVersion } },
  )
  if (data.code !== 200 || !data.data) throw new Error(data.message)
  return data.data
}

export async function getScoreJob(jobId: string): Promise<ScoreJobSnapshot> {
  const { data } = await api.get<ApiResponse<ScoreJobSnapshot>>(`/v1/songs/score/jobs/${jobId}`)
  if (data.code !== 200 || !data.data) throw new Error(data.message)
  return data.data
}

export class ScoreJobError extends Error {
  code: string

  constructor(code: string, message: string) {
    super(message)
    this.name = 'ScoreJobError'
    this.code = code
  }
}

export function isScoreLoadAbortError(err: unknown): boolean {
  if (err instanceof DOMException && err.name === 'AbortError') return true
  return err instanceof Error && err.message === '已取消谱面生成'
}

const SCORE_JOB_POLL_MS = 800
const SCORE_JOB_TIMEOUT_MS = 180_000

function throwIfAborted(signal?: AbortSignal) {
  if (signal?.aborted) {
    throw new DOMException('Aborted', 'AbortError')
  }
}

export async function loadScoreWithProgress(
  neteaseSongId: number,
  instrument: ScoreInstrument,
  vocalVersion: VocalVersion,
  onProgress: (job: ScoreJobSnapshot) => void,
  signal?: AbortSignal,
): Promise<ScoreData> {
  if (useScoreMock) {
    return getScore(neteaseSongId, instrument, vocalVersion)
  }

  throwIfAborted(signal)
  const job = await startScoreJob(neteaseSongId, instrument, vocalVersion)
  throwIfAborted(signal)
  onProgress(job)

  if (job.status === 'completed' && job.result) {
    return job.result
  }

  return await new Promise((resolve, reject) => {
    const startedAt = Date.now()
    let timer: number | null = null
    let inflight = false
    let settled = false

    const cleanup = () => {
      if (timer !== null) {
        window.clearInterval(timer)
        timer = null
      }
    }

    const finish = (handler: () => void) => {
      if (settled) return
      settled = true
      cleanup()
      handler()
    }

    const poll = async () => {
      if (settled) return
      if (signal?.aborted) {
        finish(() => reject(new DOMException('Aborted', 'AbortError')))
        return
      }
      if (Date.now() - startedAt > SCORE_JOB_TIMEOUT_MS) {
        finish(() => reject(new ScoreJobError('TIMEOUT', '曲谱生成超时，请稍后重试')))
        return
      }
      if (inflight) return
      inflight = true
      try {
        const snapshot = await getScoreJob(job.job_id)
        if (signal?.aborted) {
          finish(() => reject(new DOMException('Aborted', 'AbortError')))
          return
        }
        onProgress(snapshot)
        if (snapshot.status === 'completed' && snapshot.result) {
          finish(() => resolve(snapshot.result as ScoreData))
        } else if (snapshot.status === 'failed') {
          finish(() =>
            reject(
              new ScoreJobError(
                snapshot.error_code || 'FAILED',
                snapshot.error_message || '曲谱生成失败',
              ),
            ),
          )
        }
      } catch (err) {
        finish(() => reject(err))
      } finally {
        inflight = false
      }
    }

    timer = window.setInterval(() => {
      void poll()
    }, SCORE_JOB_POLL_MS)
    void poll()

    signal?.addEventListener(
      'abort',
      () => {
        finish(() => reject(new DOMException('Aborted', 'AbortError')))
      },
      { once: true },
    )
  })
}
