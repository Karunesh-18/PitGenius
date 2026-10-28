import { useQuery } from '@tanstack/react-query'
import { api } from './client'
import { useSeason } from './season'
import type { StrategySimulateRequest, TireDegradationRequest } from './types'


export function useDrivers() {
  const season = useSeason()
  return useQuery({ queryKey: ['drivers', season], queryFn: () => api.drivers(season) })
}

export function useDriver(driverRef: string | undefined) {
  const season = useSeason()
  return useQuery({
    queryKey: ['driver', driverRef, season],
    queryFn: () => api.driver(driverRef as string, season),
    enabled: !!driverRef,
  })
}

export function useTeams() {
  const season = useSeason()
  return useQuery({ queryKey: ['teams', season], queryFn: () => api.teams(season) })
}

export function useTeam(teamRef: string | undefined) {
  const season = useSeason()
  return useQuery({
    queryKey: ['team', teamRef, season],
    queryFn: () => api.team(teamRef as string, season),
    enabled: !!teamRef,
  })
}

export function useRaces() {
  const season = useSeason()
  return useQuery({ queryKey: ['races', season], queryFn: () => api.races(season) })
}

export function useRace(round: number | undefined) {
  const season = useSeason()
  return useQuery({
    queryKey: ['race', season, round],
    queryFn: () => api.race(season, round as number),
    enabled: !!round,
  })
}

export function useDriverStandings() {
  const season = useSeason()
  return useQuery({ queryKey: ['driverStandings', season], queryFn: () => api.driverStandings(season) })
}

export function useConstructorStandings() {
  const season = useSeason()
  return useQuery({
    queryKey: ['constructorStandings', season],
    queryFn: () => api.constructorStandings(season),
  })
}

export function useTrackOutline(circuitRef: string | undefined) {
  return useQuery({
    queryKey: ['trackOutline', circuitRef],
    queryFn: () => api.trackOutline(circuitRef as string),
    enabled: !!circuitRef,
    retry: false,
  })
}

export function useStrategySimulation(request: StrategySimulateRequest | null) {
  return useQuery({
    queryKey: ['strategySimulate', request],
    queryFn: () => api.simulateStrategy(request as StrategySimulateRequest),
    enabled: !!request,
  })
}

export function useCircuits() {
  const season = useSeason()
  return useQuery({ queryKey: ['circuits', season], queryFn: () => api.circuits(season) })
}

export function useCircuitIntelligence(circuitRef: string | undefined) {
  const season = useSeason()
  return useQuery({
    queryKey: ['circuitIntelligence', circuitRef, season],
    queryFn: () => api.circuitIntelligence(circuitRef as string, season),
    enabled: !!circuitRef,
  })
}

export function useTelemetryDrivers(round: number | undefined) {
  const season = useSeason()
  return useQuery({
    queryKey: ['telemetryDrivers', season, round],
    queryFn: () => api.telemetryDrivers(season, round as number),
    enabled: !!round,
  })
}

export function useDriverTelemetry(round: number | undefined, driverRef: string | undefined) {
  const season = useSeason()
  return useQuery({
    queryKey: ['driverTelemetry', season, round, driverRef],
    queryFn: () => api.driverTelemetry(season, round as number, driverRef as string),
    enabled: !!round && !!driverRef,
  })
}

export function useTireDegradationPrediction(request: TireDegradationRequest | null) {
  return useQuery({
    queryKey: ['tireDegradationPredict', request],
    queryFn: () => api.predictTireDegradation(request as TireDegradationRequest),
    enabled: !!request,
  })
}

export function useDriverPointsHistory(driverRef: string | undefined) {
  const season = useSeason()
  return useQuery({
    queryKey: ['driverPointsHistory', driverRef, season],
    queryFn: () => api.driverPointsHistory(driverRef as string, season),
    enabled: !!driverRef,
  })
}

export function useSeasons() {
  return useQuery({ queryKey: ['seasons'], queryFn: () => api.seasons(), staleTime: 300_000 })
}

export function useLive() {
  return useQuery({
    queryKey: ['live'],
    queryFn: () => api.live(),
    refetchInterval: 5_000,
    staleTime: 0,
  })
}
