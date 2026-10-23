import { NavLink } from 'react-router-dom'

const ITEMS = [
  { to: '/', label: 'Home', end: true },
  { to: '/drivers', label: 'Drivers' },
  { to: '/teams', label: 'Teams' },
  { to: '/strategy', label: 'Strategy' },
  { to: '/circuits', label: 'Circuits' },
]

export function NavRail() {
  return (
    <nav className="w-44 shrink-0 border-r border-hairline">
      <ul>
        {ITEMS.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `block px-4 py-3 text-sm border-l-2 transition-colors ${
                  isActive
                    ? 'border-signal text-paper bg-graphite'
                    : 'border-transparent text-steel hover:text-paper hover:bg-graphite/60'
                }`
              }
            >
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}
