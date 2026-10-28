# User guide

Open the app at http://localhost:5173 (see [setup-and-operations.md](setup-and-operations.md) to start it).

## Choosing a season
The strip at the top right lists one tick per season that has data. The selected year is shown in full (for example `2023`) and the others as two digits. A filled dot under a year means that season also has lap telemetry. Your choice is kept in the address bar (`?season=2023`), so you can share a link.

## Pages (left navigation)
1. **Home:** calendar, recent winners, podium strip, driver and constructor standings for the selected season.
2. **Drivers:** pick a driver for the rating breakdown, season stats and a points-by-round chart.
3. **Teams:** pick a team for points, wins, reliability % and the pit-efficiency estimate.
4. **Strategy:** choose circuit, starting position, tyre compound, pit lap and race length, then run the simulation. You get a predicted finish, total time, pit loss, the optimal pit lap, a lap-time curve and a plain-English explanation. The tyre-wear panel predicts lap time for a given tyre age and shows which factors mattered.
5. **Circuits:** pick a track for overtaking difficulty (0–100), Safety Car likelihood and average pit loss. Where telemetry exists (2023) the 3D track view can replay a driver's fastest lap.
6. **Live:** shows `● LIVE` while a session is running, or "Last session" otherwise. It lists positions with gap to the leader and interval, plus weather and the latest race-control messages.

## Reading the numbers
- **Driver Rating (0–100):** relative to the other drivers that season. 50 means average. It is not a career rating.
- **Reliability %:** classified finishes divided by entries.
- **Pit efficiency:** an estimate from extra time on in/out laps, not measured pit-lane time.
- **Strategy results:** a model of typical behaviour, not a forecast of an actual race.

## If a page is empty
- The selected season may have results only. Telemetry features need 2023.
- If the Live page says no session is available, OpenF1 may be briefly unreachable. It retries automatically.
