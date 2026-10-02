import { SourceBadge } from "@/components/ui/source-badge";
import { getSources } from "@/lib/data";

export default async function MethodologyPage() {
  const sources = await getSources();

  return (
    <div className="space-y-6 sm:space-y-7">
      <section>
        <div className="text-xs font-bold uppercase tracking-[0.18em] text-blue-800">
          About the data
        </div>
        <h1 className="mt-2 max-w-4xl text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl md:text-4xl">
          Understand what each number means before you use it.
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700 md:text-base">
          This page explains the labels used throughout Fin Engine in plain language and shows where each piece of information comes from.
        </p>
      </section>

      <section className="grid gap-5 xl:grid-cols-[0.82fr_1.18fr]">
        <article className="glass-panel rounded-2xl p-4 sm:p-5">
          <h2 className="text-sm font-semibold text-slate-950">Simple glossary</h2>
          <p className="mt-1 text-xs leading-5 text-slate-700">
            You do not need finance or data knowledge to use the dashboard. These are the main terms you may see.
          </p>
          <div className="mt-5 space-y-5 text-sm">
            <div>
              <div className="font-semibold text-slate-950">Listing price</div>
              <p className="mt-1 leading-6 text-slate-700">The price a seller is asking for. It does not prove that the vehicle actually sold for that amount.</p>
            </div>
            <div>
              <div className="font-semibold text-slate-950">NJKB</div>
              <p className="mt-1 leading-6 text-slate-700">An official government reference value used for vehicle-related administration and tax purposes. It is not the same as a market selling price.</p>
            </div>
            <div>
              <div className="font-semibold text-slate-950">Auction reference</div>
              <p className="mt-1 leading-6 text-slate-700">A published lower-bound or reserve-style auction value. It does not necessarily equal the final winning bid.</p>
            </div>
            <div>
              <div className="font-semibold text-slate-950">Comparable</div>
              <p className="mt-1 leading-6 text-slate-700">Another listing with the same make, model, year and location that is used to help estimate a typical asking price.</p>
            </div>
            <div>
              <div className="font-semibold text-slate-950">Observed data</div>
              <p className="mt-1 leading-6 text-slate-700">Information collected from an actual source, such as a marketplace listing stored by the analysis engine.</p>
            </div>
            <div>
              <div className="font-semibold text-slate-950">Illustrative / demo data</div>
              <p className="mt-1 leading-6 text-slate-700">Example information used only to demonstrate the interface. It should not be treated as a live market fact.</p>
            </div>
          </div>
        </article>

        <article className="glass-panel rounded-2xl p-4 sm:p-5">
          <h2 className="text-sm font-semibold text-slate-950">Where the information comes from</h2>
          <p className="mt-1 text-xs leading-5 text-slate-700">
            Every source is labelled so you can see whether it is official, observed from the market or included only for demonstration.
          </p>

          <div className="mt-5 space-y-3">
            {sources.map((source) => (
              <div key={source.id} className="glass-subpanel rounded-xl p-4">
                <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                  <div className="min-w-0">
                    <div className="break-words text-sm font-semibold text-slate-950">{source.name}</div>
                    <div className="mt-1 text-xs text-slate-700">{source.type}</div>
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
        <h2 className="text-sm font-semibold text-slate-950">What you can trust in this POC</h2>
        <div className="mt-5 grid gap-5 md:grid-cols-3">
          <article>
            <div className="text-xs font-bold uppercase tracking-[0.14em] text-emerald-800">Safe to use in the demo</div>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Source labels, official public references and marketplace estimates clearly marked as observed or demo data.
            </p>
          </article>
          <article>
            <div className="text-xs font-bold uppercase tracking-[0.14em] text-amber-800">Do not assume</div>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              A listing price is not a confirmed sale price, and illustrative auction values are not live market evidence.
            </p>
          </article>
          <article>
            <div className="text-xs font-bold uppercase tracking-[0.14em] text-blue-800">What comes next</div>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Add more authorized marketplace observations and matched government auction records, then validate the estimates against real market outcomes.
            </p>
          </article>
        </div>
      </section>
    </div>
  );
}
