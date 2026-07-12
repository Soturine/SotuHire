import { toast as sonnerToast } from "sonner";

type ToastMessage = Parameters<typeof sonnerToast.success>[0];
type ToastOptions = Parameters<typeof sonnerToast.success>[1];

function afterRender(callback: () => void) {
  if (typeof window === "undefined") return;
  window.requestAnimationFrame(() => window.setTimeout(callback, 0));
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
