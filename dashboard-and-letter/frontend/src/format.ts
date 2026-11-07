// Formatting only. The frontend never calculates money (plan.md section C).
export const pounds = (n: number) => `${n < 0 ? '−' : ''}£${Math.abs(n).toLocaleString('en-GB')}`
export const longDate = (iso: string) => {
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
}
export const sentence = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)
