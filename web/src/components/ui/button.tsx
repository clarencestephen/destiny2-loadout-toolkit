import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap font-ui font-semibold uppercase tracking-[0.18em] transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-darksith text-star border-b-2 border-sith hover:bg-sith hover:glow-sith",
        primary:
          "bg-signature-gradient text-white hover:brightness-110 hover:glow-sith",
        outline:
          "border border-border bg-transparent text-star hover:bg-nebula hover:border-sith",
        ghost: "text-star hover:bg-nebula",
        link: "text-sith underline-offset-4 hover:underline",
      },
      size: {
        default: "h-11 px-6 text-xs",
        sm: "h-9 px-4 text-[10px]",
        lg: "h-14 px-10 text-sm",
        icon: "h-11 w-11 p-0",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
