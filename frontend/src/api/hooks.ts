import { useQuery } from '@tanstack/react-query'
import { api } from './client'
import type { StrategySimulateRequest, TireDegradationRequest } from './types'

export const SEASON = 2023 // Phase 1 MVP loads a single completed season

export function useDrivers() {
  return useQuery({ queryKey: ['drivers', SEASON], queryFn: () => api.drivers(SEASON) })
}

export function useDriver(driverRef: string | undefined) {
  return useQuery({
    queryKey: ['driver', driverRef, SEASON],
    queryFn: () => api.driver(driverRef as string, SEASON),
    enabled: !!driverRef,
  })
}

export function useTeams() {
  return useQuery({ queryKey: ['teams', SEASON], queryFn: () => api.teams(SEASON) })
}

export function useTeam(teamRef: string | undefined) {
  return useQuery({
    queryKey: ['team', teamRef, SEASON],
    queryFn: () => api.team(teamRef as string, SEASON),
    enabled: !!teamRef,
  })
}

export function useRaces() {
  return useQuery({ queryKey: ['races', SEASON], queryFn: () => api.races(SEASON) })
}

export function useRace(round: number | undefined) {
  return useQuery({
    queryKey: ['race', SEASON, round],
    queryFn: () => api.race(SEASON, round as number),
    enabled: !!round,
  })
}

export function useDriverStandings() {
  return useQuery({ queryKey: ['driverStandings', SEASON], queryFn: () => api.driverStandings(SEASON) })
}

export function useConstructorStandings() {
  return useQuery({
    queryKey: ['constructorStandings', SEASON],
    queryFn: () => api.constructorStandings(SEASON),
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
  return useQuery({ queryKey: ['circuits', SEASON], queryFn: () => api.circuits(SEASON) })
}

export function useCircuitIntelligence(circuitRef: string | undefined) {
  return useQuery({
    queryKey: ['circuitIntelligence', circuitRef, SEASON],
    queryFn: () => api.circuitIntelligence(circuitRef as string, SEASON),
    enabled: !!circuitRef,
  })
}

export function useTelemetryDrivers(round: number | undefined) {
  return useQuery({
    queryKey: ['telemetryDrivers', SEASON, round],
    queryFn: () => api.telemetryDrivers(SEASON, round as number),
    enabled: !!round,
  })
}

export function useDriverTelemetry(round: number | undefined, driverRef: string | undefined) {
  return useQuery({
    queryKey: ['driverTelemetry', SEASON, round, driverRef],
    queryFn: () => api.driverTelemetry(SEASON, round as number, driverRef as string),
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
  return useQuery({
    queryKey: ['driverPointsHistory', driverRef, SEASON],
    queryFn: () => api.driverPointsHistory(driverRef as string, SEASON),
    enabled: !!driverRef,
  })
}
