import { toast } from 'sonner'

export const showToast = {
  success: (message: string, description?: string) => {
    toast.success(message, { description })
  },
  error: (message: string, description?: string) => {
    toast.error(message, { description })
  },
  warning: (message: string, description?: string) => {
    toast.warning(message, { description })
  },
  info: (message: string, description?: string) => {
    toast.info(message, { description })
  },
  loading: (message: string, description?: string) => {
    return toast.loading(message, { description })
  },
  dismiss: (id: string | number) => {
    toast.dismiss(id)
  },
  promise: <T>(
    promise: Promise<T>,
    messages: {
      loading: string
      success: string | ((data: T) => string)
      error: string | ((error: unknown) => string)
    }
  ) => {
    return toast.promise(promise, messages)
  },
}
