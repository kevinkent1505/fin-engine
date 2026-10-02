import { SourceBadge } from "@/components/ui/source-badge";
import { getSources } from "@/lib/data";

export default async function MethodologyPage() {
  const sources = await getSources();

  return (
    <div className="space-y-7">
      <section>
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-700">
          Data & methodology
        </div>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950 md:text-4xl">
          Make the evidence visible, not just the number.
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 md:text-base">
          Fin Engine is designed to retain source provenance and signal type so business users can understand what a value represents before using it in a collateral workflow.
        </p>
      </section>

      <section className="grid gap-5 xl:grid-cols-[0.82fr_1.18fr]">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold text-slate-900">Signal interpretation</h2>
          <div className="mt-5 space-y-5 text-sm">
            <div>
              <div className="font-semibold text-slate-900">Listing</div>
              <p className="mt-1 leading-6 text-slate-500">Marketplace asking price. It reflects seller expectations, not a confirmed transaction.</p>
            </div>
            <div>
              <div className="font-semibold text-slate-900">NJKB</div>
              <p className="mt-1 leading-6 text-slate-500">Official tax/reference value. Useful as a benchmark, but not a substitute for a market observation.</p>
            </div>
            <div>
              <div className="font-semibold text-slate-900">Auction limit</div>
              <p className="mt-1 leading-6 text-slate-500">Published reserve/floor-style auction signal. It is not necessarily the winning transaction price.</p>
            </div>
            <div>
              <div className="font-semibold text-slate-900">Transaction</div>
              <p className="mt-1 leading-6 text-slate-500">Reserved for future evidence of confirmed sale prices. No POC value is currently labeled as a transaction.</p>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold text-slate-900">Source registry</h2>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            The POC deliberately marks fixtures as illustrative rather than allowing them to look like live market evidence.
          </p>

          <div className="mt-5 space-y-3">
            {sources.map((source) => (
              <div key={source.id} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                  <div>
                    <div className="text-sm font-semibold text-slate-900">{source.name}</div>
                    <div className="mt-1 text-xs text-slate-500">{source.type}</div>
                  </div>
                  <SourceBadge confidence={source.confidence} />
                </div>
                <p className="mt-3 text-xs leading-5 text-slate-600">{source.note}</p>
                <div className="mt-3 text-[11px] font-medium uppercase tracking-[0.12em] text-slate-400">
                  {source.lastUpdated}
                </div>
                {source.url ? (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-3 inline-flex text-xs font-semibold text-blue-700 hover:text-blue-900"
                  >
                    Open public source ↗
                  </a>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <h2 className="text-sm font-semibold text-slate-900">POC methodology boundary</h2>
        <div className="mt-5 grid gap-5 md:grid-cols-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-700">Use now</div>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Demonstrate data provenance, business workflows, dashboard UX and how multiple signal types can be compared transparently.
            </p>
          </div>
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-amber-700">Do not claim yet</div>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Do not represent illustrative marketplace or auction fixtures as live market evidence, transaction prices or production-ready valuations.
            </p>
          </div>
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-blue-700">Next validation</div>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Connect authorized marketplace crawls, repeated observations and persisted government auction data, then validate analytical outputs against observed market behavior.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
