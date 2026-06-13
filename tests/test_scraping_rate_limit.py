from modules.scraping.rate_limit import DomainRateLimiter


def test_rate_limit_waits_between_same_domain_requests():
    times = iter([0.0, 0.0, 0.5, 1.0])
    waits = []
    limiter = DomainRateLimiter(clock=lambda: next(times), sleeper=waits.append)

    limiter.wait("https://example.com/a", 1.0)
    limiter.wait("https://example.com/b", 1.0)

    assert waits == [0.5]
