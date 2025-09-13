from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type
import httpx

retryable = retry(
    retry=retry_if_exception_type((httpx.HTTPError,)),
    wait=wait_exponential_jitter(exp_base=2, max=10),
    stop=stop_after_attempt(5),
    reraise=True,
)