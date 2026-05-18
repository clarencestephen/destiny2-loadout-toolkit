/**
 * Vader-helmet-in-triangle brand mark, per the DARTH_BANKAI guide.
 * SVG so it scales clean from favicon to hero size.
 */
export function BrandMark({ size = 48, label = "66" }: { size?: number; label?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Destiny Voyager"
      role="img"
    >
      <defs>
        <linearGradient id="dv-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%"  stopColor="#B432FF" />
          <stop offset="50%" stopColor="#FF3388" />
          <stop offset="100%" stopColor="#4411AA" />
        </linearGradient>
      </defs>
      {/* outer inverted triangle */}
      <polygon
        points="24,48 0,4 48,4"
        fill="url(#dv-grad)"
      />
      {/* inner cutout — void */}
      <polygon
        points="24,42 6,8 42,8"
        fill="#07060B"
      />
      <text
        x="24"
        y="26"
        textAnchor="middle"
        fontFamily="Orbitron, sans-serif"
        fontSize="13"
        fontWeight="900"
        fill="#E0D0F0"
        letterSpacing="1.2"
      >
        {label}
      </text>
    </svg>
  );
}
