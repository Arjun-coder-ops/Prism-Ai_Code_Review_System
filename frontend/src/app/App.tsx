import { useEffect, useState } from "react";
import type { FormEvent } from "react";

type Finding = {
  file_path: string;
  start_line: number;
  end_line: number;
  severity: string;
  title: string;
  explanation: string;
  verification_status: string;
};

type Review = {
  id: string;
  status: string;
  head_sha: string;
  findings: Finding[];
};

type AcceptedReview = Pick<Review, "id" | "status" | "head_sha">;

const pollingStatuses = new Set(["queued", "static_analyzing", "verifying"]);

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(payload?.detail ?? "PRISM could not complete that request.");
  }
  return response.json() as Promise<T>;
}

export function App() {
  const [pullRequestUrl, setPullRequestUrl] = useState("");
  const [review, setReview] = useState<Review | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!review || !pollingStatuses.has(review.status)) {
      return undefined;
    }

    let cancelled = false;
    const loadStatus = async () => {
      try {
        const response = await fetch(`/api/v1/reviews/${review.id}`);
        const nextReview = await readJson<Review>(response);
        if (!cancelled) {
          setReview(nextReview);
        }
      } catch (caughtError) {
        if (!cancelled) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "PRISM could not retrieve review status.",
          );
        }
      }
    };

    void loadStatus();
    const interval = window.setInterval(() => void loadStatus(), 2_000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [review]);

  async function submitReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await fetch("/api/v1/reviews", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pull_request_url: pullRequestUrl }),
      });
      const accepted = await readJson<AcceptedReview>(response);
      setReview({ ...accepted, findings: [] });
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "PRISM could not submit that review.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main>
      <p className="eyebrow" aria-label="Product name">
        PRISM
      </p>
      <h1>Evidence-backed pull request review</h1>
      <p>
        Submit a public GitHub pull request. PRISM queues deterministic analysis
        first and shows only findings tied to source evidence.
      </p>

      <form onSubmit={submitReview}>
        <label htmlFor="pull-request-url">Public GitHub pull request URL</label>
        <div className="submission-row">
          <input
            id="pull-request-url"
            name="pull-request-url"
            onChange={(event) => setPullRequestUrl(event.target.value)}
            placeholder="https://github.com/owner/repository/pull/123"
            required
            type="url"
            value={pullRequestUrl}
          />
          <button disabled={isSubmitting} type="submit">
            {isSubmitting ? "Queueing…" : "Review pull request"}
          </button>
        </div>
      </form>

      {error ? <p role="alert">{error}</p> : null}

      {review ? (
        <section aria-labelledby="review-status-heading" className="review-status">
          <h2 id="review-status-heading">Review status: {review.status}</h2>
          <p>
            Review <code>{review.id}</code> · head <code>{review.head_sha}</code>
          </p>
          {review.status === "completed" && review.findings.length === 0 ? (
            <p>No deterministic, evidence-backed findings were identified.</p>
          ) : null}
          <ul aria-label="Verified findings">
            {review.findings.map((finding) => (
              <li key={`${finding.file_path}:${finding.start_line}:${finding.title}`}>
                <strong>{finding.title}</strong> ({finding.severity}) — {finding.file_path}:
                {finding.start_line}–{finding.end_line}. {finding.explanation} [{finding.verification_status}]
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </main>
  );
}
