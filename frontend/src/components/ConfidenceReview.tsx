import type { ClaimAssessment } from "../types/research";

export function ConfidenceReview({ claims }: { claims: ClaimAssessment[] }) {
  if (claims.length === 0) return null;

  return (
    <section className="confidence">
      <div className="section-title">
        <h2>Claim Verification</h2>
        <span>{claims.length} scored claims</span>
      </div>
      <div className="claim-list">
        {claims.map((claim, index) => (
          <article className="claim-row" key={`${claim.claim}-${index}`}>
            <span className={`badge ${claim.confidence.toLowerCase()}`}>{claim.confidence}</span>
            <p>{claim.claim}</p>
            <small>{claim.score.toFixed(3)} cosine similarity</small>
          </article>
        ))}
      </div>
    </section>
  );
}

