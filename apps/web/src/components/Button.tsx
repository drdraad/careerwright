import { type ButtonHTMLAttributes, forwardRef, type ReactNode, useId } from "react";
import { Glyph, type GlyphName } from "./Glyph";

/** `accept` and `undo` are the two decisions on a proposed change, colour coded as well as
 *  worded (session 2, C3); neither is ever the view's primary action. */
type Variant = "primary" | "secondary" | "quiet" | "icon" | "accept" | "undo";

type Props = Omit<ButtonHTMLAttributes<HTMLButtonElement>, "disabled"> & {
  variant?: Variant;
  glyph?: GlyphName;
  /** Why the action is unavailable. A disabled button always says why, beside it. */
  disabledReason?: string;
  children?: ReactNode;
};

/**
 * One primary action per view (docs/design/README.md): use `primary` only for the decision in
 * focus. Disabled buttons stay focusable (`aria-disabled`) so their reason can be read.
 */
export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { variant = "secondary", glyph, disabledReason, children, onClick, type = "button", ...rest },
  ref,
) {
  const reasonId = useId();
  const disabled = disabledReason !== undefined;
  return (
    <>
      <button
        ref={ref}
        type={type}
        className={`btn btn-${variant}`}
        aria-disabled={disabled || undefined}
        aria-describedby={disabled ? reasonId : undefined}
        onClick={disabled ? (event) => event.preventDefault() : onClick}
        {...rest}
      >
        {glyph !== undefined && <Glyph name={glyph} />}
        {children}
      </button>
      {disabled && (
        <span id={reasonId} className="small muted ml-8">
          {disabledReason}
        </span>
      )}
    </>
  );
});
