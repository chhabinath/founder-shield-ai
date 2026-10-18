export function LandingScreen({ onStart }: { onStart: () => void }) {
  return (
    <section className="landing">
      <h1 className="landing__title">Turn a vague problem into a build-ready brief</h1>
      <p className="landing__subtitle">
        A privacy-first voice interview that separates confirmed facts from
        claims, assumptions, and unknowns — and never shares anything
        without your explicit approval.
      </p>
      <button type="button" className="landing__cta" onClick={onStart}>
        Start Interview
      </button>
    </section>
  );
}
