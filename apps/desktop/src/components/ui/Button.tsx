import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "destructive";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  isLoading?: boolean;
  children: ReactNode;
}

export function Button({ children, className = "", isLoading = false, variant = "secondary", ...props }: ButtonProps) {
  return (
    <button className={`button button-${variant} ${className}`} disabled={props.disabled || isLoading} {...props}>
      {isLoading ? <span className="spinner" aria-hidden="true" /> : children}
    </button>
  );
}
