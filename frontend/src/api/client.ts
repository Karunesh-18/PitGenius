async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}${body ? `: ${body}` : ''}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  seasons: () => request<{ season: number; has_telemetry: boolean }[]>('/races/seasons'),
  live: () => request<import('./types').LiveSnapshot>('/live/session'),
  drivers: (season?: number) =>
    request<import('./types').DriverSummary[]>(`/drivers${season ? `?season=${season}` : ''}`),
  driver: (driverRef: string, season?: number) =>
    request<import('./types').DriverDetail>(`/drivers/${driverRef}${season ? `?season=${season}` : ''}`),
  teams: (season?: number) =>
    request<import('./types').TeamSummary[]>(`/teams${season ? `?season=${season}` : ''}`),
  team: (teamRef: string, season?: number) =>
    request<import('./types').TeamDetail>(`/teams/${teamRef}${season ? `?season=${season}` : ''}`),
  races: (season?: number) =>
    request<import('./types').RaceSummary[]>(`/races${season ? `?season=${season}` : ''}`),
  race: (season: number, round: number) =>
    request<import('./types').RaceDetail>(`/races/${season}/${round}`),
  driverStandings: (season?: number) =>
    request<import('./types').DriverStandingRow[]>(`/standings/drivers${season ? `?season=${season}` : ''}`),
  constructorStandings: (season?: number) =>
    request<import('./types').ConstructorStandingRow[]>(
      `/standings/constructors${season ? `?season=${season}` : ''}`,
    ),
  circuit: (circuitRef: string) => request<import('./types').CircuitOut>(`/circuits/${circuitRef}`),
  trackOutline: (circuitRef: string) =>
    request<import('./types').TrackOutlineOut>(`/circuits/${circuitRef}/track-outline`),
  simulateStrategy: (body: import('./types').StrategySimulateRequest) =>
    request<import('./types').StrategySimulateResponse>('/strategy/simulate', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  circuits: (season?: number) =>
    request<import('./types').CircuitSummary[]>(`/circuits${season ? `?season=${season}` : ''}`),
  circuitIntelligence: (circuitRef: string, season?: number) =>
    request<import('./types').CircuitIntelligenceOut>(
      `/circuits/${circuitRef}/intelligence${season ? `?season=${season}` : ''}`,
    ),
  telemetryDrivers: (season: number, round: number) =>
    request<import('./types').TelemetryAvailabilityRow[]>(`/races/${season}/${round}/telemetry`),
  driverTelemetry: (season: number, round: number, driverRef: string) =>
    request<import('./types').TelemetryOut>(`/races/${season}/${round}/telemetry/${driverRef}`),
  predictTireDegradation: (body: import('./types').TireDegradationRequest) =>
    request<import('./types').TireDegradationResponse>('/tire-degradation/predict', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  driverPointsHistory: (driverRef: string, season?: number) =>
    request<import('./types').PointsHistoryPoint[]>(
      `/drivers/${driverRef}/points-history${season ? `?season=${season}` : ''}`,
    ),
}
