import { OrbitControls } from '@react-three/drei'
import { Canvas } from '@react-three/fiber'
import { useMemo } from 'react'
import * as THREE from 'three'
import { useTrackOutline } from '../api/hooks'
import { EmptyState, LoadingState } from '../components/StateViews'
import type { TelemetryPoint, TrackOutlinePoint } from '../api/types'

/** Track plane (FastF1 X/Y) maps to the ground (Three.js X/Z);
 * elevation (Z) maps to Three.js Y (up) — server-normalized, so scale is consistent.
 * Shared by the static ribbon and any per-driver telemetry curve so both live in
 * the same coordinate frame. */
export function buildTrackCurve(points: TrackOutlinePoint[]): THREE.CatmullRomCurve3 {
  const vectors = points.map((p) => new THREE.Vector3(p.x, p.z, p.y))
  return new THREE.CatmullRomCurve3(vectors, true, 'catmullrom', 0.2)
}

function TrackRibbon({ points, accent }: { points: TrackOutlinePoint[]; accent: string }) {
  const tubeGeometry = useMemo(() => {
    const curve = buildTrackCurve(points)
    return new THREE.TubeGeometry(curve, Math.max(points.length, 200), 1.1, 8, true)
  }, [points])

  return (
    <mesh geometry={tubeGeometry}>
      <meshStandardMaterial color="#1b212c" roughness={0.85} metalness={0.1} emissive={accent} emissiveIntensity={0.12} />
    </mesh>
  )
}

/** A small emissive sphere tracing a driver's own telemetry lap. Builds its own
 * curve from the telemetry points (same coordinate convention as the ribbon),
 * finds the two points bracketing `elapsedMs`, and interpolates a curve
 * parameter between them each frame. */
export function CarMarker({
  telemetry,
  elapsedMs,
  color,
}: {
  telemetry: TelemetryPoint[]
  elapsedMs: number
  color: string
}) {
  const curve = useMemo(() => buildTrackCurve(telemetry), [telemetry])

  const position = useMemo(() => {
    if (telemetry.length < 2) return new THREE.Vector3(0, 0, 0)

    let idx = 0
    while (idx < telemetry.length - 1 && telemetry[idx + 1].time_ms <= elapsedMs) idx++
    const a = telemetry[idx]
    const b = telemetry[Math.min(idx + 1, telemetry.length - 1)]
    const span = b.time_ms - a.time_ms
    const frac = span > 0 ? Math.min(1, Math.max(0, (elapsedMs - a.time_ms) / span)) : 0
    const fracIndex = idx + frac
    const u = Math.min(1, Math.max(0, fracIndex / (telemetry.length - 1)))

    return curve.getPointAt(u)
  }, [telemetry, elapsedMs, curve])

  return (
    <mesh position={position}>
      <sphereGeometry args={[1.5, 16, 16]} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={2.2} toneMapped={false} />
    </mesh>
  )
}

interface Track3DViewProps {
  circuitRef: string
  accent?: string
  /** Optional — when provided (alongside elapsedMs), renders a CarMarker
   * tracing this driver's lap on top of the static ribbon. Omit for the
   * existing static-track-only usage (e.g. Strategy Simulator). */
  telemetry?: TelemetryPoint[]
  elapsedMs?: number
  driverColor?: string
}

export function Track3DView({ circuitRef, accent = '#ff3b30', telemetry, elapsedMs = 0, driverColor }: Track3DViewProps) {
  const outline = useTrackOutline(circuitRef)
  const hasOutline = !!outline.data && outline.data.points.length > 0
  const hasTelemetry = !!telemetry && telemetry.length > 0

  // The outline is what gives the scene its scale and frame of reference, so it
  // gates the whole view: a CarMarker drawn without a ribbon is just a glowing
  // sphere in a black void. Behavior is identical to before for callers that
  // pass no telemetry at all (e.g. Strategy Simulator).
  if (outline.isLoading) return <LoadingState label="Loading track" />
  if (!hasOutline) {
    return <EmptyState message="No 3D track outline generated for this circuit yet." />
  }

  return (
    <div className="h-72 bg-asphalt">
      <Canvas camera={{ position: [0, 90, 90], fov: 45 }}>
        <color attach="background" args={['#0c0f14']} />
        <ambientLight intensity={0.5} />
        <directionalLight position={[60, 100, 40]} intensity={1.1} />
        <TrackRibbon points={outline.data!.points} accent={accent} />
        {hasTelemetry && <CarMarker telemetry={telemetry!} elapsedMs={elapsedMs} color={driverColor ?? accent} />}
        <OrbitControls enablePan={false} minDistance={40} maxDistance={220} />
      </Canvas>
    </div>
  )
}
