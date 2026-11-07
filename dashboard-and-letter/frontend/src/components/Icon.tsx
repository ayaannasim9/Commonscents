// Authored SVG icons, one stroke style (2px, round). Decorative by default: callers put the words beside them.
const P: Record<string, string> = {
  check: 'M5 12.5l4.5 4.5L19 7.5',
  'check-circle': 'M12 21a9 9 0 100-18 9 9 0 000 18zM8 12.5l3 3 5-6',
  triangle: 'M12 4L2.8 19.5h18.4L12 4zM12 10v4.5M12 17.2v.1',
  cross: 'M12 21a9 9 0 100-18 9 9 0 000 18zM9 9l6 6M15 9l-6 6',
  talk: 'M4 5h16v11H10l-4.5 4v-4H4V5zM8 10h8',
  shield: 'M12 3l7.5 3v5.5c0 4.5-3.2 8-7.5 9.5-4.3-1.5-7.5-5-7.5-9.5V6L12 3zM8.5 12l2.5 2.5 4.5-5',
  speaker: 'M4 9.5v5h4l5 4v-13l-5 4H4zM16.5 9a4 4 0 010 6M18.8 6.5a7.5 7.5 0 010 11',
  stop: 'M7 7h10v10H7z',
  info: 'M12 21a9 9 0 100-18 9 9 0 000 18zM12 11v5.5M12 7.8v.1',
}
export function Icon({ name, size = 24 }: { name: keyof typeof P | string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d={P[name]} />
    </svg>
  )
}
