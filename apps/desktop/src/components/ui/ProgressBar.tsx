interface ProgressBarProps {
  value: number;
  label?: string;
}

export function ProgressBar({ label, value }: ProgressBarProps) {
  return (
    <div className="progress-block">
      {label && (
        <div className="progress-label">
          <span>{label}</span>
          <span>{value}%</span>
        </div>
      )}
      <div className="progress-track" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={value}>
        <span className="progress-fill" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
