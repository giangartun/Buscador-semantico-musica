interface ResultCardProps {
  title: string;
  description?: string;
  classes?: string[];
  source: string;
  uri?: string;
}

export default function ResultCard({
  title,
  description,
  classes = [],
  source,
  uri,
}: ResultCardProps) {
  const sourceIsDbpedia = source.includes('DBpedia');

  return (
    <div className="group bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800 overflow-hidden hover:border-slate-300 dark:hover:border-slate-700 transition-colors duration-200">
      <div className="px-5 pt-5 pb-4 border-b border-slate-100 dark:border-slate-800 flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className="w-10 h-10 flex-shrink-0 rounded-lg bg-violet-50 dark:bg-violet-950/40 flex items-center justify-center">
            <span className="text-violet-600 dark:text-violet-400 text-lg">♪</span>
          </div>

          <div className="min-w-0">
            <h3 className="text-base font-medium text-slate-900 dark:text-white leading-tight truncate">
              {title}
            </h3>

            <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
              Fuente: {source}
            </p>
          </div>
        </div>

        {classes.length > 0 && (
          <span className="flex-shrink-0 mt-1 inline-block px-2.5 py-1 text-xs font-medium text-violet-700 dark:text-violet-300 bg-violet-50 dark:bg-violet-950/40 border border-violet-200 dark:border-violet-800/60 rounded-full">
            {classes[0]}
          </span>
        )}
      </div>

      {(description || classes.length > 1 || uri) && (
        <div className="px-5 py-4 flex flex-col gap-4">
          {description && (
            <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              {description}
            </p>
          )}

          {classes.length > 1 && (
            <div>
              <p className="text-[11px] font-medium uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-2">
                Categorías
              </p>

              <div className="flex flex-wrap gap-1.5">
                {classes.slice(1).map((clase) => (
                  <span
                    key={clase}
                    className="px-2.5 py-1 text-xs font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md"
                  >
                    {clase}
                  </span>
                ))}
              </div>
            </div>
          )}

          {sourceIsDbpedia && uri && (
            <a
              href={uri}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center justify-center gap-1.5 py-2.5 px-4 text-sm font-medium text-violet-700 dark:text-violet-300 bg-violet-50 dark:bg-violet-950/40 border border-violet-200 dark:border-violet-800/60 rounded-lg hover:bg-violet-100 dark:hover:bg-violet-900/40 hover:border-violet-300 dark:hover:border-violet-700 transition-colors duration-150 active:scale-[0.99]"
            >
              Ver en DBpedia
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M7 17 17 7M7 7h10v10" />
              </svg>
            </a>
          )}
        </div>
      )}
    </div>
  );
}