interface ResultCardProps {
  title: string;
  description?: string;
  classes?: string[];
  source: string;
  uri?: string;
  abstract?: string;
  birthDate?: string;
  deathDate?: string;
  genres?: string[];
  instruments?: string[];
  birthPlaces?: string[];
  nationalities?: string[];
  notableWorks?: string[];
  thumbnail?: string;
  wikipediaPage?: string;
}

export default function ResultCard({
  title,
  description,
  classes = [],
  source,
  uri,
  abstract,
  birthDate,
  deathDate,
  genres,
  instruments,
  birthPlaces,
  nationalities,
  notableWorks,
  thumbnail,
  wikipediaPage,
}: ResultCardProps) {
  const sourceIsDbpedia = source.includes('DBpedia');
  const hasExtraDbpedia =
    sourceIsDbpedia &&
    (abstract || birthDate || deathDate || (genres && genres.length > 0) ||
      (instruments && instruments.length > 0) ||
      (birthPlaces && birthPlaces.length > 0) ||
      (nationalities && nationalities.length > 0) ||
      (notableWorks && notableWorks.length > 0) ||
      thumbnail || wikipediaPage);

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

      {hasExtraDbpedia && (
        <div className="px-5 pb-5">
          <div className="border border-slate-100 dark:border-slate-800 rounded-lg p-4 bg-slate-50/40 dark:bg-slate-900/40">
            <p className="text-[11px] font-medium uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3">
              Detalle DBpedia
            </p>

            {thumbnail && (
              <img
                src={thumbnail}
                alt={title}
                className="w-full max-h-56 object-contain rounded-md mb-3"
                loading="lazy"
              />
            )}

            {abstract && (
              <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed mb-3">
                {abstract}
              </p>
            )}

            {(birthDate || deathDate) && (
              <div className="text-xs text-slate-500 dark:text-slate-400 mb-3">
                {birthDate && <span>Nacimiento: {birthDate}</span>}
                {birthDate && deathDate && <span> · </span>}
                {deathDate && <span>Fallecimiento: {deathDate}</span>}
              </div>
            )}

            {genres && genres.length > 0 && (
              <div className="mb-3">
                <p className="text-xs text-slate-400 dark:text-slate-500 mb-1">
                  Generos
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {genres.map((genre) => (
                    <span
                      key={genre}
                      className="px-2.5 py-1 text-xs font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md"
                    >
                      {genre}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {instruments && instruments.length > 0 && (
              <div className="mb-3">
                <p className="text-xs text-slate-400 dark:text-slate-500 mb-1">
                  Instrumentos
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {instruments.map((instrument) => (
                    <span
                      key={instrument}
                      className="px-2.5 py-1 text-xs font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md"
                    >
                      {instrument}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {birthPlaces && birthPlaces.length > 0 && (
              <div className="mb-3">
                <p className="text-xs text-slate-400 dark:text-slate-500 mb-1">
                  Lugar de nacimiento
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {birthPlaces.map((place) => (
                    <span
                      key={place}
                      className="px-2.5 py-1 text-xs font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md"
                    >
                      {place}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {nationalities && nationalities.length > 0 && (
              <div className="mb-3">
                <p className="text-xs text-slate-400 dark:text-slate-500 mb-1">
                  Nacionalidad
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {nationalities.map((nation) => (
                    <span
                      key={nation}
                      className="px-2.5 py-1 text-xs font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md"
                    >
                      {nation}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {notableWorks && notableWorks.length > 0 && (
              <div className="mb-3">
                <p className="text-xs text-slate-400 dark:text-slate-500 mb-1">
                  Obras destacadas
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {notableWorks.map((work) => (
                    <span
                      key={work}
                      className="px-2.5 py-1 text-xs font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md"
                    >
                      {work}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {wikipediaPage && (
              <a
                href={wikipediaPage}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-violet-600 dark:text-violet-400 hover:underline"
              >
                Ver en Wikipedia
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}