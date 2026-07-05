export const CAREERPILOT_LOGO_SRC = "/careerpilot-logo.png";

type BrandLogoProps = {
  variant?: "nav" | "full";
  className?: string;
  alt?: string;
};

export function BrandLogo({
  variant = "nav",
  className = "",
  alt = "CareerPilot",
}: BrandLogoProps) {
  return (
    <img
      src={CAREERPILOT_LOGO_SRC}
      alt={alt}
      className={`brand-logo brand-logo--${variant}${className ? ` ${className}` : ""}`}
      decoding="async"
    />
  );
}
