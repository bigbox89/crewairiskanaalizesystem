/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'risk-red': '#ff0000',
        'risk-yellow': '#ffff00',
        'risk-green': '#00ff00',
        'bubble-blue': '#1d4ed8',
        'bubble-gray': '#374151',
      },
    },
  },
  plugins: [],
};

