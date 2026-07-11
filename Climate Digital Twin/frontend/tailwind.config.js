/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        void: "#05070d",
        glass: "rgba(13, 20, 33, 0.65)",
        cyanAccent: "#00e5ff",
        blueAccent: "#2979ff",
        greenAccent: "#00e676",
        amberAccent: "#ffb300",
        redAccent: "#ff3d57",
        textPrimary: "#e8f1ff",
        textMuted: "#7d8aa3",
      },
      fontFamily: {
        sans: ['Space Grotesk', 'Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
