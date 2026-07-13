import { toast as sonnerToast } from "sonner";

type ToastMessage = Parameters<typeof sonnerToast.success>[0];
type ToastOptions = Parameters<typeof sonnerToast.success>[1];

function afterRender(callback: () => void) {
  if (typeof window === "undefined") return;
  const run = () => window.setTimeout(callback, 0);
  const idleCallback = (
    window as unknown as { requestIdleCallback?: Window["requestIdleCallback"] }
  ).requestIdleCallback;
  if (idleCallback) {
    idleCallback.call(window, run, { timeout: 250 });
    return;
  }
  // Safari versions without requestIdleCallback still get two completed
  // paint opportunities before Sonner updates its external store. This avoids
  // cross-component updates while a lazy route or Radix primitive is rendering.
  window.requestAnimationFrame(() => window.requestAnimationFrame(run));
}

export const toast = {
  message(message: ToastMessage, options?: ToastOptions) {
    afterRender(() => sonnerToast(message, options));
  },
  success(message: ToastMessage, options?: ToastOptions) {
    afterRender(() => sonnerToast.success(message, options));
  },
  error(message: ToastMessage, options?: ToastOptions) {
    afterRender(() => sonnerToast.error(message, options));
  },
  warning(message: ToastMessage, options?: ToastOptions) {
    afterRender(() => sonnerToast.warning(message, options));
  },
  info(message: ToastMessage, options?: ToastOptions) {
    afterRender(() => sonnerToast.info(message, options));
  },
};
