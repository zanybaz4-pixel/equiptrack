export const DEPARTMENT_NAME = "Mechanical Technology Department";

export default function DepartmentLogo({ className, width = 104, height = 104, decorative = false }) {
  return (
    <img
      className={className}
      src="/images/mechanical-technology-logo.png"
      alt={decorative ? "" : `${DEPARTMENT_NAME} logo`}
      width={width}
      height={height}
    />
  );
}
