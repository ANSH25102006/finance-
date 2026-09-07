/**
 * lib/errorUtils.ts
 * Safely extracts human-readable error messages from Axios / FastAPI error responses,
 * network errors, and Pydantic 422 detail arrays.
 */

export function extractErrorMessage(
  err: unknown,
  fallback: string = 'Something went wrong. Please try again.'
): string {
  if (!err) return fallback

  const axiosErr = err as {
    response?: {
      status?: number
      data?: {
        detail?: string | Array<{ msg?: string; loc?: string[] }> | Record<string, unknown>
      }
    }
    message?: string
  }

  // Network or Connection Error
  if (!axiosErr.response) {
    if (
      axiosErr.message === 'Network Error' ||
      axiosErr.message?.includes('Network') ||
      axiosErr.message?.includes('ECONNREFUSED')
    ) {
      return 'Unable to connect to the backend server. Please verify the server is running.'
    }
    return axiosErr.message || fallback
  }

  const detail = axiosErr.response.data?.detail

  // Simple string detail (e.g., 400 Bad Request, 401 Unauthorized)
  if (typeof detail === 'string') {
    return detail
  }

  // FastAPI / Pydantic validation error array (422 Unprocessable Entity)
  if (Array.isArray(detail)) {
    const messages = detail
      .map((d) => {
        if (typeof d === 'string') return d
        if (d && typeof d.msg === 'string') return d.msg
        return null
      })
      .filter((msg): msg is string => Boolean(msg))

    if (messages.length > 0) {
      return messages.join('. ')
    }
  }

  // Object detail fallback
  if (detail && typeof detail === 'object') {
    return JSON.stringify(detail)
  }

  return fallback
}
