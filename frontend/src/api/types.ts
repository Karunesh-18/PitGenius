export interface RatingBreakdown {
  qualifying_pace: number
  race_pace: number
  consistency: number
  finishes: number
}

export interface DriverSummary {
  driver_ref: string
  code: string | null
  given_name: string
  family_name: string
  team_ref: string | null
  team_name: string | null
  points: number
  wins: number
  driver_rating: number
  rating_breakdown: RatingBreakdown
}

export interface DriverRaceResultRow {
  round: number
  race_name: string
  grid_position: number | null
  finish_position: number | null
  status: string
  points: number
}

export interface DriverDetail extends DriverSummary {
  nationality: string | null
  date_of_birth: string | null
  headshot_url: string | null
  results: DriverRaceResultRow[]
}

export interface PointsHistoryPoint {
  round: number
  points: number
  position: number
}

export interface TeammateComparison {
  driver_ref: string
  code: string | null
  given_name: string
  family_name: string
  points: number
  avg_finish_position: number | null
  avg_qualifying_position: number | null
}

export interface TeamSummary {
  team_ref: string
  name: string
  color_primary: string | null
  color_secondary: string | null
  points: number
  wins: number
  reliability_pct: number | null
  pit_efficiency_estimate_s: number | null
}

export interface TeamDetail extends TeamSummary {
  drivers: TeammateComparison[]
}

export interface RaceSummary {
  season: number
  round: number
  name: string
  circuit_ref: string
  race_date: string
  status: 'upcoming' | 'completed'
  country: string | null
  winner_driver_ref: string | null
  winner_code: string | null
  winner_team_ref: string | null
}

export interface QualifyingResultRow {
  position: number | null
  driver_ref: string
  code: string | null
  team_ref: string
  q1_ms: number | null
  q2_ms: number | null
  q3_ms: number | null
}

export interface RaceResultRow {
  finish_position: number | null
  grid_position: number | null
  driver_ref: string
  code: string | null
  team_ref: string
  status: string
  points: number
  fastest_lap_rank: number | null
  final_compound: string | null
}

export interface RaceDetail extends RaceSummary {
  qualifying_results: QualifyingResultRow[]
  race_results: RaceResultRow[]
}

export interface DriverStandingRow {
  position: number
  driver_ref: string
  code: string | null
  given_name: string
  family_name: string
  team_ref: string | null
  points: number
  wins: number
}

export interface ConstructorStandingRow {
  position: number
  team_ref: string
  name: string
  points: number
  wins: number
}

export interface CircuitOut {
  circuit_ref: string
  name: string
  country: string | null
  length_km: number | null
}

export interface TrackOutlinePoint {
  x: number
  y: number
  z: number
}

export interface TrackOutlineOut {
  circuit_ref: string
  points: TrackOutlinePoint[]
}

export interface StrategySimulateRequest {
  circuit_ref: string
  starting_position: number
  tire_compound: 'SOFT' | 'MEDIUM' | 'HARD' | 'INTERMEDIATE' | 'WET'
  pit_lap: number
  num_laps: number
}

export interface LapTimePoint {
  lap: number
  lap_time_s: number
}

export interface StrategySimulateResponse {
  predicted_finish_position: number
  total_time_estimate_s: number
  pit_loss_s: number
  optimal_pit_lap: number
  lap_time_curve: LapTimePoint[]
  explanation: string
}

export interface CircuitSummary {
  circuit_ref: string
  name: string
  country: string | null
  length_km: number | null
}

export interface CircuitIntelligenceOut {
  circuit_ref: string
  season: number
  overtaking_index: number
  safety_car_probability_pct: number
  avg_pit_loss_s: number | null
  races_analyzed: number
}

export interface TelemetryAvailabilityRow {
  driver_ref: string
  code: string | null
  lap_number: number
  lap_time_ms: number | null
}

export interface TelemetryPoint {
  point_index: number
  distance_m: number
  time_ms: number
  speed_kph: number | null
  throttle_pct: number | null
  brake: boolean | null
  gear: number | null
  drs: number | null
  x: number
  y: number
  z: number
}

export interface TelemetryOut {
  season: number
  round: number
  driver_ref: string
  code: string | null
  lap_number: number
  lap_time_ms: number | null
  points: TelemetryPoint[]
}

export interface TireDegradationRequest {
  circuit_ref: string
  compound: 'SOFT' | 'MEDIUM' | 'HARD' | 'INTERMEDIATE' | 'WET'
  tyre_life: number
}

export interface ShapContribution {
  feature: string
  value: string
  shap_value_s: number
}

export interface TireDegradationResponse {
  predicted_lap_time_s: number
  baseline_lap_time_s: number
  degradation_vs_fresh_s: number
  shap_contributions: ShapContribution[]
  explanation: string
}
