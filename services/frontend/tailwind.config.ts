
import type { Config } from 'tailwindcss'

export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: 'hsl(0 0% 100%)',
        foreground: 'hsl(222.2 84% 4.9%)',
        muted: 'hsl(210 40% 96%)',
        card: 'hsl(0 0% 100%)',
        primary: {
          DEFAULT: 'hsl(222.2 47.4% 11.2%)',
        },
      },
    },
  },
  plugins: [],
} satisfies Config
