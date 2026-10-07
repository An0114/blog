"""性能压测脚本：并发请求动态列表与详情接口，输出 P50 / P95 / P99 耗时。

用法：
  python scripts/bench_posts.py [--base http://127.0.0.1:8000] [--workers 20] [--requests 200]

统计口径：每请求从发出到响应体接收完成的端到端耗时（毫秒）。
"""

import argparse
import concurrent.futures
import random
import statistics
import time

import httpx

LIST_URL = "/api/posts"
DETAIL_URL_TMPL = "/api/posts/{post_id}"


def _timed(client: httpx.Client, method: str, url: str) -> float:
    start = time.perf_counter()
    resp = client.request(method, url)
    resp.raise_for_status()
    return (time.perf_counter() - start) * 1000


def run(base: str, workers: int, requests: int) -> dict[str, dict[str, float]]:
    results: dict[str, list[float]] = {"list": [], "detail": []}

    def worker(_: int) -> None:
        with httpx.Client(base_url=base, timeout=30) as client:
            for _ in range(requests):
                page = random.randint(1, 100)
                results["list"].append(_timed(client, "GET", f"{LIST_URL}?page={page}&size=10"))
                post_id = random.randint(1, 1000)
                results["detail"].append(_timed(client, "GET", DETAIL_URL_TMPL.format(post_id=post_id)))

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(worker, range(workers)))

    summary = {}
    for name, lat in results.items():
        lat.sort()
        n = len(lat)
        summary[name] = {
            "n": n,
            "p50": round(lat[int(n * 0.50) - 1], 1),
            "p95": round(lat[int(n * 0.95) - 1], 1),
            "p99": round(lat[int(n * 0.99) - 1], 1),
            "avg": round(statistics.mean(lat), 1),
        }
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--requests", type=int, default=100)
    args = parser.parse_args()
    s = run(args.base, args.workers, args.requests)
    for name, row in s.items():
        print(f"{name:>6}: n={row['n']} p50={row['p50']}ms p95={row['p95']}ms p99={row['p99']}ms avg={row['avg']}ms")
