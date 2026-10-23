import { useCallback, useEffect, useRef, useState } from 'react'

/** Drives an elapsedMs value forward via requestAnimationFrame using real
 * delta time, looping back to 0 at lapDurationMs. Deliberately implemented
 * with rAF rather than R3F's useFrame so it's usable outside a <Canvas> too —
 * the elapsedMs value it produces gets passed down as a prop into Track3DView. */
export function useTelemetryPlayback(lapDurationMs: number) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [elapsedMs, setElapsedMs] = useState(0)
  const rafRef = useRef<number | null>(null)
  const lastTsRef = useRef<number | null>(null)
  const scrubbingRef = useRef(false)
  const durationRef = useRef(lapDurationMs)
  durationRef.current = lapDurationMs

  const tick = useCallback((ts: number) => {
    if (lastTsRef.current == null) lastTsRef.current = ts
    const delta = ts - lastTsRef.current
    lastTsRef.current = ts

    // While the user is dragging the scrubber, the loop keeps running but stops
    // writing elapsedMs — otherwise it would overwrite the dragged value 60×/sec
    // and the thumb would snap away from the cursor.
    if (!scrubbingRef.current) {
      const duration = Math.max(durationRef.current, 1)
      setElapsedMs((prev) => {
        const next = prev + delta
        return next >= duration ? next % duration : next
      })
    }

    rafRef.current = requestAnimationFrame(tick)
  }, [])

  const play = useCallback(() => {
    if (rafRef.current != null) return
    lastTsRef.current = null
    setIsPlaying(true)
    rafRef.current = requestAnimationFrame(tick)
  }, [tick])

  const pause = useCallback(() => {
    if (rafRef.current != null) cancelAnimationFrame(rafRef.current)
    rafRef.current = null
    lastTsRef.current = null
    setIsPlaying(false)
  }, [])

  const scrubTo = useCallback((ms: number) => {
    const duration = Math.max(durationRef.current, 1)
    setElapsedMs(Math.min(Math.max(ms, 0), duration))
  }, [])

  /** Suspends the playback tick for the duration of a scrub gesture, so a drag
   * tracks the pointer. Playback resumes from the scrubbed position on end. */
  const beginScrub = useCallback(() => {
    scrubbingRef.current = true
  }, [])

  const endScrub = useCallback(() => {
    scrubbingRef.current = false
    lastTsRef.current = null
  }, [])

  useEffect(() => {
    return () => {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current)
    }
  }, [])

  return { isPlaying, elapsedMs, play, pause, scrubTo, beginScrub, endScrub }
}
