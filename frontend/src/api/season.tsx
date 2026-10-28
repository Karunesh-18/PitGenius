import { createContext, useContext, useState, type ReactNode } from 'react'

const DEFAULT_SEASON = 2023 // fully loaded (results, laps, telemetry) in both Neon and the archive

const SeasonContext = createContext<[number, (s: number) => void]>([DEFAULT_SEASON, () => {}])

/** Selected season lives in context and mirrors to ?season= so a year is shareable by URL. */
export function SeasonProvider({ children }: { children: ReactNode }) {
  const [season, setSeasonState] = useState(() => {
    const n = Number(new URLSearchParams(window.location.search).get('season'))
    return n >= 1950 ? n : DEFAULT_SEASON
  })
  const setSeason = (s: number) => {
    setSeasonState(s)
    const url = new URL(window.location.href)
    url.searchParams.set('season', String(s))
    window.history.replaceState(null, '', url)
  }
  return <SeasonContext.Provider value={[season, setSeason]}>{children}</SeasonContext.Provider>
}

export const useSeasonState = () => useContext(SeasonContext)
export const useSeason = () => useContext(SeasonContext)[0]
