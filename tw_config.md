tailwind.config = {
  theme: {
    extend: {
      colors: {
        // Palm — deep jungle green, dark surfaces (sidebar, hero bands)
        palm: {
          50: '#EAF1EC', 100: '#CADBD0', 200: '#9FBFAC', 300: '#6B9C82',
          400: '#427458', 500: '#275A40', 600: '#1B4D36', 700: '#163E2C',
          800: '#0F2E21', 900: '#0B2218', 950: '#071A12'
        },
        // Leaf — vivid action green, the primary brand/CTA color
        leaf: {
          50: '#EFF8F1', 100: '#D7EFDD', 200: '#AFDFC0', 300: '#7FCB9C',
          400: '#4FB37A', 500: '#2E9A5F', 600: '#257F4D', 700: '#1D6840',
          800: '#175134', 900: '#123F29'
        },
        // Pepper — warm red-orange, urgency / destructive / alerts
        pepper: {
          50: '#FDEEEA', 100: '#F9D2C7', 200: '#F2A78F', 300: '#EB7C57',
          400: '#E25E37', 500: '#D6481F', 600: '#B83A16', 700: '#942D10',
          800: '#70210C', 900: '#4D1608'
        },
        // Jollof — gold, price emphasis & highlights
        jollof: {
          50: '#FCF5E6', 100: '#F7E6BF', 200: '#EFCD85', 300: '#E6B454',
          400: '#DC9F35', 500: '#C98826', 600: '#A66D1C', 700: '#825416',
          800: '#5F3D10', 900: '#3D270A'
        },
        // Sand — warm neutral background
        sand: { 50: '#FEFCF8', 100: '#FBF7EF', 200: '#F5EEDD', 300: '#EDE2C8' },
        // Ink — warm neutral text scale
        ink: {
          50: '#F6F5F3', 100: '#E8E6E1', 200: '#D1CDC4', 300: '#B3ADA0',
          400: '#8B8576', 500: '#6B6557', 600: '#534E42', 700: '#3F3B32',
          800: '#2B2823', 900: '#1C1A16'
        }
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"Plus Jakarta Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace']
      },
      boxShadow: {
        card: '0 1px 2px rgba(28,26,22,0.05), 0 10px 28px -14px rgba(28,26,22,0.18)',
        pop: '0 8px 30px -8px rgba(11,34,24,0.35)'
      }
    }
  }
}