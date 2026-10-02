import { SourceBadge } from "@/components/ui/source-badge";
import { getSources } from "@/lib/data";

export default async function MethodologyPage() {
  const sources = await getSources();

  return (
    <div className="space-y-6 sm:space-y-7">
      <section>
        <div className="text-xs font-bold uppercase tracking-[0.18em] text-blue-800">
          Data & methodology
        </div>
        <h1 className="mt-2 max-w-4xl text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl md:text-4xl">
          Make the evidence visible, not just the number.
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700 md:text-base">
          Fin Engine is designed to retain source provenance and signal type so business users can understand what a value represents before using it in a collateral workflow.
        </p>
      </section>

      <section className="grid gap-5 xl:grid-cols-[0.82fr_1.18fr]">
        <article className="glass-panel rounded-2xl p-4 sm:p-5">
          <h2 className="text-sm font-semibold text-slate-950">Signal interpretation</h2>
          <div className="mt-5 space-y-5 text-sm">
            <div>
              <div className="font-semibold text-slate-950">Listing</div>
              <p className="mt-1 leading-6 text-slate-600">Marketplace asking price. It reflects seller expectations, not a confirmed transaction.</p>
            </div>
            <div>
              <div className="font-semibold text-slate-950">NJKB</div>
              <p className="mt-1 leading-6 text-slate-600">Official tax/reference value. Useful as a benchmark, but not a substitute for a market observation.</p>
            </div>
            <div>
              <div className="font-semibold text-slate-950">Auction limit</div>
              <p className="mt-1 leading-6 text-slate-600">Published reserve/floor-style auction signal. It is not necessarily the winning transaction price.</p>
            </div>
            <div>
              <div className="font-semibold text-slate-950">Transaction</div>
              <p className="mt-1 leading-6 text-slate-600">Reserved for future evidence of confirmed sale prices. No POC value is currently labeled as a transaction.</p>
            </div>
          </div>
        </article>

        <article className="glass-panel rounded-2xl p-4 sm:p-5">
          <h2 className="text-sm font-semibold text-slate-950">Source registry</h2>
          <p className="mt-1 text-xs leading-5 text-slate-600">
            The POC deliberately marks fixtures as illustrative rather than allowing them to look like live market evidence.
          </p>

          <div className="mt-5 space-y-3">
            {sources.map((source) => (
              <div key={source.id} className="glass-subpanel rounded-xl p-4">
                <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                  <div className="min-w-0">
                    <div className="break-words text-sm font-semibold text-slate-950">{source.name}</div>
                    <div className="mt-1 text-xs text-slate-600">{source.type}</div>
                  </div>
                  <div className="shrink-0">
                    <SourceBadge confidence={source.confidence} />
                  </div>
                </div>
                <p className="mt-3 text-xs leading-5 text-slate-700">{source.note}</p>
                <div className="mt-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-600">
                  {source.lastUpdated}
                </div>
                {source.url ? (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-3 inline-flex min-h-11 items-center rounded-lg text-xs font-bold text-blue-800 underline decoration-blue-300 underline-offset-4 hover:text-blue-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-700 focus-visible:ring-offset-2"
                  >
                    Open public source
                    <span aria-hidden="true" className="ml-1">↗</span>
                    <span className="sr-only"> in a new tab</span>
                  </a>
                ) : null}
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="glass-panel rounded-2xl p-4 sm:p-5">
        <h2 className="text-sm font-semibold text-slate-950">POC methodology boundary</h2>
        <div className="mt-5 grid gap-5 md:grid-cols-3">
          <article>
            <div className="text-xs font-bold uppercase tracking-[0.14em] text-emerald-800">Use now</div>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Demonstrate data provenance, business workflows, dashboard UX and how multiple signal types can be compared transparently.
            </p>
          </article>
          <article>
            <div className="text-xs font-bold uppercase tracking-[0.14em] text-amber-800">Do not claim yet</div>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Do not represent illustrative marketplace or auction fixtures as live market evidence, transaction prices or production-ready valuations.
            </p>
          </article>
          <article>
            <div className="text-xs font-bold uppercase tracking-[0.14em] text-blue-800">Next validation</div>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Connect authorized marketplace crawls, repeated observations and persisted government auction data, then validate analytical outputs against observed market behavior.
            </p>
          </article>
        </div>
      </section>
    </div>
  );
}
