export async function api(path, signal, options = {}) {
  let response;
  try {
    const timeout = AbortSignal.timeout(15000);
    response = await fetch(`/api${path}`, {
      ...options,
      signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
      headers: { Accept: "application/json", ...options.headers },
    });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new Error(
      error.name === "TimeoutError"
        ? "The connection took too long. Please try again."
        : "Unable to connect to EquipTrack. Please try again.",
    );
  }
  let body;
  try {
    body = await response.json();
  } catch (error) {
    if (signal?.aborted) throw error;
    if (response.ok) {
      throw new Error(
        error.name === "TimeoutError" || error.name === "AbortError"
          ? "The connection took too long. Please try again."
          : "Unable to read the response. Please try again.",
      );
    }
  }
  if (!response.ok) {
    const error = new Error(
      body?.error?.message || "Unable to connect. Please try again.",
    );
    error.status = response.status;
    if (response.status === 401 && !path.startsWith("/auth/")) {
      window.dispatchEvent(new Event("equiptrack:session-expired"));
    }
    throw error;
  }
  return body;
}
