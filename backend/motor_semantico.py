import os
import re
import unicodedata
from owlready2 import *

# Configuración de la ruta de la ontología
ruta_ontologia = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ontology", "musica.owl"))

# Variables globales para persistencia en memoria RAM y optimización de velocidad
_onto_instancia = None
_serialized_cache = {}

# Prefijos semánticos típicos a remover para limpiar la interfaz del frontend
PREFIXES_TO_REMOVE = ["Inst_", "Art_", "Gen_", "Alb_", "Can_", "Obra_", "Aut_"]
SUPPORTED_LANGS = {"es", "en", "fr"}

LANGUAGE_HINTS = {
    "es": {
        "acordeon", "aerofono", "arpa", "autor", "barroco", "baja", "cancion",
        "clasico", "clarinete", "composicion", "composiciones", "compositor",
        "concierto", "cuerda", "cuerdas", "facil", "flauta", "guitarra",
        "instrumento", "instrumentos", "mandolina", "metal", "musico", "obra",
        "obras", "percusion", "piano", "romantico", "saxofon", "sinfonia",
        "sonata", "teclado", "trombon", "trompeta", "viento", "violin",
    },
    "en": {
        "accordion", "aerophone", "author", "baroque", "clarinet", "classic",
        "classical", "composition", "compositions", "composer", "concerto",
        "easy", "flute", "guitar", "harp", "instrument", "instruments",
        "keyboard", "mandolin", "metal", "music", "musician", "percussion",
        "piece", "pieces", "piano", "romantic", "saxophone", "song", "sonata",
        "string", "strings", "symphony", "trombone", "trumpet", "violin",
        "wind", "work", "works",
    },
    "fr": {
        "accordeon", "aerophone", "auteur", "baroque", "chanson", "clarinette",
        "classique", "compositeur", "composition", "compositions", "concerto",
        "corde", "cordes", "facile", "flute", "guitare", "harpe",
        "instrument", "instruments", "mandoline", "metal", "morceau",
        "morceaux", "musicien", "oeuvre", "oeuvres", "percussion", "piano",
        "romantique", "saxophone", "sonate", "symphonie", "trombone",
        "trompette", "vent", "violon",
    },
}

LANGUAGE_RAW_HINTS = {
    "es": {
        "acordeón", "aerófono", "canción", "clásico", "composición",
        "fácil", "músico", "percusión", "romántico", "saxofón",
        "sinfonía", "trombón", "violín",
    },
    "fr": {
        "à", "flûte", "flûtes", "métal", "métaux", "œuvre", "œuvres",
        "pièce", "prélude", "préludes",
    },
}

LANGUAGE_STOPWORDS = {
    "es": {"de", "del", "la", "el", "los", "las", "para", "por", "con"},
    "en": {"of", "by", "the", "for", "with", "and"},
    "fr": {"de", "des", "du", "la", "le", "les", "pour", "avec", "et"},
}

LANGUAGE_EXACT_OVERRIDES = {
    "violin": "en",
    "flute": "en",
    "trumpet": "en",
    "clarinet": "en",
    "harp": "en",
    "keyboard": "en",
    "string": "en",
    "strings": "en",
    "wind": "en",
    "work": "en",
    "works": "en",
}

SYNONYMS = {
    # Instrumentos (ES / EN / FR)
    "violin": ["violin", "violines", "violín", "fiddle", "violins", "violon", "violons"],
    "piano": ["piano", "pianos", "pianoforte"],
    "guitarra": ["guitarra", "guitarras", "guitar", "guitars", "guitare", "guitares"],
    "flauta": ["flauta", "flautas", "flute", "flutes", "flûte", "flûtes"],
    "oboe": ["oboe", "oboes", "hautbois"],
    "trompeta": ["trompeta", "trompetas", "trumpet", "trumpets", "trompette", "trompettes"],
    "clarinete": ["clarinete", "clarinetes", "clarinet", "clarinets", "clarinette", "clarinettes"],
    "teclado": ["teclado", "teclados", "keyboard", "keyboards", "piano", "pianos", "clavier", "claviers"],
    "arpa": ["arpa", "arpas", "harp", "harps", "harpe", "harpes"],
    "cimbalum": ["cimbalum", "cimbales", "cimbalom", "cimbals", "cymbalum", "cymbales", "cymbal", "cymbals"],
    "clavicordio": ["clavicordio", "clavicordios", "clavichord", "clavichords", "clavicorde", "clavicordes"],
    "contrabajo": ["contrabajo", "contrabajos", "double bass", "double basses", "contrebasse", "contrebasses"],
    "mandolina": ["mandolina", "mandolinas", "mandolin", "mandolins", "mandoline", "mandolines"],
    "corno": ["corno", "corni", "horn", "horns", "cor", "cors"],
    "saxofon": ["saxofon", "saxofones", "saxophone", "saxophones", "saxophone", "saxophones"],
    "trombon": ["trombon", "trombones", "trombone", "trombones", "trombone", "trombones"],
    "tuba": ["tuba", "tubas", "tuba", "tubas", "tuba", "tubas"],
    "aerofono": ["aerofono", "aerofonos", "aerophone", "aerophones", "aérophone", "aérophones"],
    # Familias y Categorías (ES / EN / FR)
    "percusion": ["percusion", "percusión", "percussion", "percussions", "drums"],
    "cuerda": ["cuerda", "cuerdas", "string", "strings", "corde", "cordes"],
    "viento": ["viento", "vientos", "wind", "winds", "brass", "vent", "vents"],
    "viento madera": ["viento madera", "woodwind", "woodwinds", "bois"],
    "madera": ["madera", "wood", "bois"],
    "metal": ["metal", "metales", "metal", "métal", "métaux"],        
    # Periodos Históricos (ES / EN / FR)
    "romantico": ["romantico", "romántico", "romantic", "romanticism", "romantique", "romantisme"],
    "barroco": ["barroco", "baroque"],
    "clasico": ["clasico", "clásico", "classical", "classic", "classique"],
    # Conceptos Generales de la Ontología (ES / EN / FR)
    "composicion": ["composicion", "composición", "composition", "piece", "work", "track", "music", "œuvre", "oeuvre", "morceau"],
    "composiciones": ["composiciones", "compositions", "pieces", "works", "tracks", "œuvres", "oeuvres", "morceaux"],
    "fantasía": ["fantasia", "fantasía", "fantasy", "fantaisie"],
    "artista": ["artista", "musico", "músico", "autor", "creador", "artist", "composer", "author", "compositeur", "auteur"],
    "sinfonia": ["sinfonia", "sinfonía", "symphony", "symphonies", "symphonie", "symphonies"],
    "sonata": ["sonata", "sonatas", "sonate"],
    
    # Niveles de dificultad (ES / EN / FR)
    "alta": ["alta", "alto", "high", "hard", "complex", "difficult", "avanzado", "advanced", "haute", "complexe", "difficile"],
    "media": ["media", "medio", "medium", "intermediate", "normal", "moyenne", "intermédiaire"],
    "baja": ["baja", "bajo", "low", "easy", "simple", "facil", "fácil", "basse", "facile"]
}

DOMAIN_TRANSLATIONS = {
    "en": {
        "Acústico": "Acoustic",
        "Requiere Afinación": "Requires tuning",
        "Polifónica": "Polyphonic",
        "Compositor": "Composer",
        "Obra": "Work",
        "Instrumento": "Instrument",
        "Capacidad": "Capability",
        "Thing": "Thing",
        "Instrumento_Cuerda": "String instrument",
        "Instrumento_Viento": "Wind instrument",
        "Instrumento_Percusion": "Percussion instrument",
        "Instrumento_Teclado": "Keyboard instrument",
        "Sinfonia": "Symphony",
        "Sinfonía": "Symphony",
        "Concierto": "Concerto",
        "Sonata": "Sonata",
        "Fuga": "Fugue",
        "Tocata": "Toccata",
        "Primavera": "Spring",
        "Lago de los Cisnes": "Swan Lake",
        "Claro de Luna": "Moonlight",
        "Cascanueces": "Nutcracker",
        "Danza Hada": "Fairy Dance",
        "Violin": "Violin",
        "Violín": "Violin",
        "Violin Solista": "Solo violin",
        "Piano Cola": "Grand piano",
        "Flauta": "Flute",
        "Guitarra": "Guitar",
        "Clarinete": "Clarinet",
        "Trompeta": "Trumpet",
        "Trombon": "Trombone",
        "Trombón": "Trombone",
        "Tuba": "Tuba",
        "Fagot": "Bassoon",
        "Corno Frances": "French horn",
        "Arpa": "Harp",
        "Contrabajo": "Double bass",
        "Viola": "Viola",
        "Violonchelo": "Cello",
        "Timbal": "Timpani",
        "Transposicion": "Transposition",
        "Transposición": "Transposition",
        "Organo": "Organ",
        "Órgano": "Organ",
        "Acordeon": "Accordion",
        "Acordeón": "Accordion",
        "Cuerda": "String",
        "Cuerdas": "Strings",
        "Viento": "Wind",
        "Percusion": "Percussion",
        "Percusión": "Percussion",
        "Romantico": "Romantic",
        "Romántico": "Romantic",
        "Clasico": "Classical",
        "Clásico": "Classical",
        "Barroco": "Baroque",
        "Alta": "High",
        "Media": "Medium",
        "Baja": "Low",
    },
    "fr": {
        "Acústico": "Acoustique",
        "Requiere Afinación": "Accord requis",
        "Polifónica": "Polyphonique",
        "Compositor": "Compositeur",
        "Obra": "Oeuvre",
        "Instrumento": "Instrument",
        "Capacidad": "Capacité",
        "Thing": "Entité",
        "Instrumento_Cuerda": "Instrument à cordes",
        "Instrumento_Viento": "Instrument à vent",
        "Instrumento_Percusion": "Instrument de percussion",
        "Instrumento_Teclado": "Instrument à clavier",
        "Sinfonia": "Symphonie",
        "Sinfonía": "Symphonie",
        "Concierto": "Concerto",
        "Sonata": "Sonate",
        "Fuga": "Fugue",
        "Tocata": "Toccata",
        "Primavera": "Printemps",
        "Lago de los Cisnes": "Lac des cygnes",
        "Claro de Luna": "Clair de lune",
        "Cascanueces": "Casse-noisette",
        "Danza Hada": "Danse de la fee",
        "Violin": "Violon",
        "Violín": "Violon",
        "Violin Solista": "Violon soliste",
        "Piano Cola": "Piano à queue",
        "Flauta": "Flûte",
        "Guitarra": "Guitare",
        "Clarinete": "Clarinette",
        "Trompeta": "Trompette",
        "Trombon": "Trombone",
        "Trombón": "Trombone",
        "Tuba": "Tuba",
        "Fagot": "Basson",
        "Corno Frances": "Cor",
        "Arpa": "Harpe",
        "Contrabajo": "Contrebasse",
        "Viola": "Alto",
        "Violonchelo": "Violoncelle",
        "Timbal": "Timbales",
        "Transposicion": "Transposition",
        "Transposición": "Transposition",
        "Organo": "Orgue",
        "Órgano": "Orgue",
        "Acordeon": "Accordeon",
        "Acordeón": "Accordeon",
        "Cuerda": "Corde",
        "Cuerdas": "Cordes",
        "Viento": "Vent",
        "Percusion": "Percussion",
        "Percusión": "Percussion",
        "Romantico": "Romantique",
        "Romántico": "Romantique",
        "Clasico": "Classique",
        "Clásico": "Classique",
        "Barroco": "Baroque",
        "Alta": "Haute",
        "Media": "Moyenne",
        "Baja": "Basse",
    },
}

DESCRIPTION_TRANSLATIONS = {
    "guitarra": {
        "en": "Harmonic plucked-string instrument. Its immense sonic versatility allows it to range from the polyphony of academic music to serving as the fundamental rhythmic and harmonic engine of pop and rock.",
        "fr": "Instrument harmonique à cordes pincées. Son immense polyvalence sonore lui permet d'aller de la polyphonie de la musique savante jusqu'au rôle de moteur rythmique et harmonique fondamental de la pop et du rock.",
    },
    "arpa": {
        "en": "Harmonic plucked-string instrument with a triangular frame. It produces sound through the vibration of strings plucked with the fingers, adding arpeggiated textures, fluid glissandos and ethereal chords to any ensemble.",
        "fr": "Instrument harmonique à cordes pincées doté d'un cadre triangulaire. Il produit le son par la vibration des cordes pincées avec les doigts, apportant des textures arpégées, des glissandos fluides et des accords éthérés à tout ensemble.",
    },
    "clarinete": {
        "en": "Single-reed woodwind instrument with a cylindrical tube. It has extraordinary technical agility and an expansive dynamic range, from deep low notes to penetrating highs.",
        "fr": "Instrument à vent en bois à anche simple et tube cylindrique. Il possède une agilité technique extraordinaire et une large plage dynamique, des graves profonds aux aigus pénétrants.",
    },
    "flauta": {
        "en": "Reedless woodwind instrument that produces sound through air friction against an edge. Its outstanding agility and bright tone often lead the upper melodic section of the orchestra.",
        "fr": "Instrument à vent en bois sans anche qui produit le son par la friction de l'air contre un biseau. Son agilité remarquable et son timbre brillant dirigent souvent la section mélodique aiguë de l'orchestre.",
    },
    "violin": {
        "en": "High-register bowed string instrument. Together, first and second violin sections form the main melodic core that guides the structure of symphonic works.",
        "fr": "Instrument à cordes frottées au registre aigu. Ensemble, les pupitres de premiers et seconds violons constituent le noyau mélodique principal qui guide la structure des œuvres symphoniques.",
    },
    "Violin_Solista": {
        "en": "Member of the classical string family, distinguished by its configuration and superior acoustic projection, intended for principal melodies and passages of extreme technical virtuosity.",
        "fr": "Membre de la famille des cordes classiques, remarquable par sa configuration et sa projection acoustique supérieure, destiné aux mélodies principales et aux passages d'une virtuosité technique extrême.",
    },
    "Acordeon_Cromatico": {
        "en": "Portable aerophone instrument with bellows and free reeds. It has keyboards on both sides, allowing the performer to play complex melodies and harmonic accompaniments simultaneously.",
        "fr": "Instrument aérophone portable avec soufflet et anches libres. Il possède des claviers des deux côtés, permettant à l'interprète de jouer simultanément des mélodies complexes et des accompagnements harmoniques.",
    },
    "Arpa_Concierto": {
        "en": "Large plucked-string instrument with a complex pedal system. It offers immense harmonic richness and is essential for glissando effects and ethereal orchestral textures.",
        "fr": "Grand instrument à cordes pincées doté d'un système complexe de pédales. Il offre une immense richesse harmonique et reste essentiel pour les effets de glissando et les textures orchestrales éthérées.",
    },
    "Bajo_Electrico_Fender": {
        "en": "Fundamental electropohonic plucked-string instrument in modern instrumentation. Its magnetic pickups convert string vibration into an electric signal, providing the harmonic and rhythmic foundation.",
        "fr": "Instrument électrophonique à cordes pincées fondamental dans l'instrumentation moderne. Ses micros magnétiques convertissent la vibration des cordes en signal électrique, fournissant la base harmonique et rythmique.",
    },
    "Celesta_Orquestal": {
        "en": "Percussive keyboard instrument whose felt-covered hammers strike metal plates over resonating boxes. It produces a crystalline and unmistakably magical sound.",
        "fr": "Instrument à clavier percuté dont les marteaux recouverts de feutre frappent des lames métalliques placées sur des caisses de résonance. Il produit un son cristallin et magique inimitable.",
    },
    "Corno_Frances": {
        "en": "Brass wind instrument with coiled conical tubing and rotary valves. It acts as a perfect timbral bridge between the woodwind and brass families thanks to its warm, round and majestic sound.",
        "fr": "Instrument à vent de cuivre avec tube conique enroulé et valves rotatives. Il agit comme un pont timbral idéal entre les bois et les cuivres grâce à son son chaud, rond et majestueux.",
    },
    "Violonchelo_ArcoTradicional": {
        "en": "Low-register bowed string instrument. Its timbre is the closest to the human voice, making it crucial as a solo, melodic and basso continuo instrument.",
        "fr": "Instrument à cordes frottées au registre grave. Son timbre est l'un des plus proches de la voix humaine, ce qui le rend essentiel comme instrument soliste, mélodique et de basse continue.",
    },
    "Corno_Ingles": {
        "en": "Double-reed woodwind instrument closely related to the oboe, but with a lower register and pear-shaped bell. It is noted for its deeply melancholic timbre.",
        "fr": "Instrument à vent en bois à anche double, étroitement apparenté au hautbois mais avec un registre plus grave et un pavillon piriforme. Il se distingue par son timbre profondément mélancolique.",
    },
    "Aerofono_DobleCana": {
        "en": "Woodwind instrument fitted with a double reed. Its penetrating, expressive and stable sound makes it the universal standard for tuning the symphony orchestra.",
        "fr": "Instrument à vent en bois muni d'une anche double. Son son pénétrant, expressif et stable en fait la référence universelle pour l'accord de l'orchestre symphonique.",
    },
    "Fagot": {
        "en": "Low woodwind instrument with a double reed and a long folded tube. It provides the harmonic base of the woodwind section, standing out for its dark, resonant tone and great technical agility.",
        "fr": "Instrument grave de la famille des bois, avec anche double et long tube replié. Il fournit la base harmonique de la section des bois et se distingue par son timbre sombre, résonant et sa grande agilité technique.",
    },
    "Timbal_Orquestal": {
        "en": "Tunable membrane percussion instrument made of a large copper bowl and a pedal tension system. It is the rhythmic and harmonic pillar of symphonic percussion, capable of producing a resonant bass and dramatic crescendos.",
        "fr": "Instrument de percussion à membrane accordable composé d'une grande cuve en cuivre et d'un système de tension à pédales. Il constitue le pilier rythmique et harmonique de la percussion symphonique, capable de produire une basse résonante et des crescendos dramatiques.",
    },
    "Organo_Tubos": {
        "en": "Majestic keyboard and aerophone instrument. It controls pressurized air through sets of pipes of different registers using multiple manuals and a pedalboard.",
        "fr": "Majestueux instrument à clavier et aérophone. Il contrôle le passage de l'air sous pression à travers des ensembles de tuyaux de différents registres au moyen de plusieurs claviers manuels et d'un pédalier.",
    },
    "Piano_Cola_Steinway": {
        "en": "Keyboard and struck-string instrument of the highest mechanical demand. Its sophisticated escapement action and large soundboard allow absolute control of dynamics, from the most delicate pianissimo to overwhelming resonance.",
        "fr": "Instrument à clavier et cordes frappées d'une grande exigence mécanique. Son mécanisme d'échappement sophistiqué et sa vaste table d'harmonie permettent un contrôle absolu des nuances, du pianissimo le plus délicat à la résonance la plus ample.",
    },
    "Saxofon_Alto": {
        "en": "Woodwind instrument with a single-reed mouthpiece and a conical brass body. Its mid-high register and vocal expressiveness make it a protagonist in contemporary orchestras and popular music.",
        "fr": "Instrument à vent en bois avec bec à anche simple et corps conique en laiton. Son registre médium-aigu et son expressivité vocale remarquable en font un protagoniste des orchestres contemporains comme de la musique populaire.",
    },
    "Saxofon_Tenor": {
        "en": "Member of the saxophone family with a lower and more imposing register. Its robust, velvety sound is a fundamental pillar for melodic solos and the foundation of modern ensembles.",
        "fr": "Membre de la famille des saxophones avec un registre plus grave et imposant. Sa sonorité robuste et veloutée est un pilier essentiel des solos mélodiques et de la base des ensembles modernes.",
    },
    "Trombon": {
        "en": "Brass wind instrument that uses a telescopic slide to change tube length and pitch. Its sound is powerful and it is the only brass instrument capable of pure continuous glissandos.",
        "fr": "Instrument à vent de cuivre qui utilise une coulisse télescopique pour modifier la longueur du tube et la hauteur. Son son est puissant et c'est le seul cuivre capable de réaliser de purs glissandos continus.",
    },
    "Trompeta": {
        "en": "The highest-pitched brass instrument, operated by valves or pistons. Its bright, directional timbre gives it a dominant role in symphonic fanfares, heroic passages and principal melodies.",
        "fr": "L'instrument le plus aigu de la famille des cuivres, actionné par valves ou pistons. Son timbre brillant et directionnel lui donne un rôle dominant dans les fanfares symphoniques, les passages héroïques et les mélodies principales.",
    },
    "Tuba": {
        "en": "The largest and lowest brass instrument in the orchestra. It uses a complex system of pistons or valves to provide the fundamental harmonic and rhythmic support of the brass section.",
        "fr": "Le plus grand et le plus grave des cuivres de l'orchestre. Il utilise un système complexe de pistons ou de valves pour fournir le soutien harmonique et rythmique fondamental de la section des cuivres.",
    },
    "Antonio_Vivaldi": {
        "en": "Italian composer and violinist of the Baroque period, a key figure in the development of the solo concerto. His mastery of string composition was immortalized in his famous series of concertos, The Four Seasons.",
        "fr": "Compositeur et violoniste italien de la période baroque, figure clé du développement du concerto soliste. Sa maîtrise de l'écriture pour cordes a été immortalisée dans sa célèbre série de concertos, Les Quatre Saisons.",
    },
    "Astor_Piazzolla": {
        "en": "Argentine bandoneonist and composer, creator of Nuevo Tango. He revolutionized the traditional genre by incorporating elements of jazz and classical music with innovative instrumentations including electric guitars, pianos and strings.",
        "fr": "Bandoneoniste et compositeur argentin, créateur du Nuevo Tango. Il a révolutionné le genre traditionnel en intégrant des éléments de jazz et de musique classique avec des instrumentations innovantes incluant guitares électriques, pianos et cordes.",
    },
    "Niccolo_Paganini": {
        "en": "Italian Romantic composer and virtuoso violinist. His dazzling technique, extreme speed and innovative use of harmonics and pizzicato set a definitive new standard for solo violin performance.",
        "fr": "Compositeur romantique et violoniste virtuose italien. Sa technique éblouissante, sa vitesse extrême et son usage novateur des harmoniques et du pizzicato ont établi un nouveau standard pour l'exécution du violon soliste.",
    },
    "Wolfgang_Amadeus_Mozart": {
        "en": "Austrian Classical-period composer and unmatched child prodigy. His prolific output covers every genre of his time with formal perfection, elegance and melodic brilliance that remain central to the academic repertoire.",
        "fr": "Compositeur autrichien de la période classique et enfant prodige incomparable. Son œuvre prolifique couvre tous les genres de son époque avec une perfection formelle, une élégance et une brillance mélodique toujours centrales dans le répertoire savant.",
    },
    "Pyotr_Ilyich_Tchaikovsky": {
        "en": "Russian Romantic composer, renowned for his unmatched melodic gift and masterful symphonic orchestration. He wrote some of history's most iconic ballets, integrating complete families of instruments with unique drama.",
        "fr": "Compositeur russe de la période romantique, célèbre pour son talent mélodique exceptionnel et son orchestration symphonique magistrale. Il est l'auteur de ballets parmi les plus emblématiques de l'histoire, intégrant des familles instrumentales complètes avec un dramatisme unique.",
    },
    "Franz_Liszt": {
        "en": "Hungarian Romantic composer and virtuoso pianist. He pushed piano technique to unprecedented levels, explored the instrument's acoustic resources to the fullest and created the symphonic poem format for orchestra.",
        "fr": "Compositeur romantique hongrois et pianiste virtuose. Il porta la technique du piano à des niveaux sans précédent, explora au maximum les ressources acoustiques de l'instrument et créa le format du poème symphonique pour orchestre.",
    },
    "Frederic_Chopin": {
        "en": "Polish-French Romantic composer and virtuoso pianist. His work is almost entirely devoted to solo piano, noted for deep expressiveness, harmonic innovation and brilliant technique that redefined the instrument's repertoire.",
        "fr": "Compositeur romantique franco-polonais et pianiste virtuose. Son œuvre est presque entièrement consacrée au piano solo, remarquable par son expressivité profonde, son innovation harmonique et sa technique brillante qui ont redéfini le répertoire de l'instrument.",
    },
    "Jean_Michel_Jarre": {
        "en": "French composer and producer, a worldwide pioneer of electronic music. He is known for the massive integration of analog synthesizers, sequencers and electroacoustic technology to create complex avant-garde soundscapes.",
        "fr": "Compositeur et producteur français, pionnier mondial de la musique électronique. Il est célèbre pour l'intégration massive de synthétiseurs analogiques, de séquenceurs et de technologies électroacoustiques dans des paysages sonores complexes et avant-gardistes.",
    },
    "Johann_Sebastian_Bach": {
        "en": "German Baroque composer and organist, considered one of the greatest geniuses in music history. He brought counterpoint and fugue to their summit, leaving a vast and structurally perfect body of work for keyboard, strings and ensembles.",
        "fr": "Compositeur et organiste allemand de la période baroque, considéré comme l'un des plus grands génies de l'histoire musicale. Il porta l'art du contrepoint et de la fugue à son sommet, laissant une vaste œuvre structurellement parfaite pour clavier, cordes et ensembles.",
    },
    "Ludwig_van_Beethoven": {
        "en": "German composer and pianist, a vital transitional figure between the Classical and Romantic eras. His symphonic works and sonatas redefined Western music, marking a turning point in emotional intensity and architectural complexity.",
        "fr": "Compositeur et pianiste allemand, figure de transition essentielle entre les époques classique et romantique. Son œuvre symphonique et ses sonates ont redéfini la musique occidentale, marquant un tournant dans l'intensité émotionnelle et la complexité architecturale.",
    },
    "Sergei_Rachmaninoff": {
        "en": "Russian post-Romantic composer, pianist and conductor. His style is characterized by deep melancholic lyricism, dense harmonies and extremely difficult textures designed to exploit the full sonority of the modern piano.",
        "fr": "Compositeur, pianiste et chef d'orchestre russe post-romantique. Son style se caractérise par un lyrisme mélancolique profond, des harmonies denses et des textures d'une difficulté extrême conçues pour exploiter toute la sonorité du piano moderne.",
    },
    "s_sinte_jupiter": {
        "en": "Classic analog polyphonic synthesizer. Known for dense layers of multiple oscillators, warm filters and its ability to create orchestral electronic textures and enveloping atmospheres.",
        "fr": "Synthétiseur polyphonique analogique classique. Il est connu pour ses couches denses de multiples oscillateurs, ses filtres chaleureux et sa capacité à créer des textures orchestrales électroniques et des atmosphères enveloppantes.",
    },
    "s_sinte_moog": {
        "en": "Legendary monophonic analog synthesizer. It revolutionized modern music through voltage-control design, producing deep bass frequencies and powerful electronic solos.",
        "fr": "Synthétiseur analogique monophonique légendaire. Il a révolutionné la musique moderne grâce à sa conception à contrôle par tension, produisant des basses profondes et des solos électroniques puissants.",
    },
    "s_sintetizador_analogico": {
        "en": "Electrophonic instrument that generates sound through analog circuits. It shapes the sound wave by manipulating frequencies and voltages, allowing infinite artificial timbres to be created from scratch.",
        "fr": "Instrument électrophonique générant le son au moyen de circuits analogiques. Il modèle l'onde sonore par la manipulation des fréquences et des tensions, permettant de créer depuis zéro une infinité de timbres artificiels.",
    },
    "Cimbalum_CuerdaPercutida": {
        "en": "Traditional instrument with a large trapezoidal resonating box. It is played by striking the strings directly with handheld mallets, producing a highly resonant folk timbre used often in Eastern European music and contemporary ensembles.",
        "fr": "Instrument traditionnel composé d'une grande caisse de résonance trapézoïdale. Il se joue en frappant directement les cordes avec de petits maillets, produisant un timbre folklorique très résonant, souvent utilisé dans la musique d'Europe de l'Est et les ensembles contemporains.",
    },
    "Clavicordio_CuerdaPercutida": {
        "en": "Historical keyboard instrument in which strings are struck by small metal tangents. It is notable as the only early keyboard instrument that lets the performer apply subtle mechanical vibrato and slight direct dynamic variations.",
        "fr": "Instrument à clavier historique dans lequel les cordes sont frappées par de petites tangentes métalliques. Il se distingue comme le seul clavier ancien permettant à l'interprète d'appliquer un subtil vibrato mécanique et de légères variations dynamiques directes.",
    },
    "Contrabajo_ArcoTradicional": {
        "en": "The lowest and largest bowed string instrument. It supports the harmonic foundations of the orchestra and is equally indispensable in modern ensembles through pizzicato technique.",
        "fr": "L'instrument à cordes frottées le plus grave et volumineux. Il soutient les fondations harmoniques de l'orchestre et reste tout aussi indispensable dans les ensembles modernes grâce à la technique du pizzicato.",
    },
    "Glockenspiel_Studio": {
        "en": "Pitched percussion instrument made of tuned steel bars. When struck with hard or metal mallets, it produces a bright, penetrating bell-like timbre ideal for highlighting high melodies over dense orchestral textures.",
        "fr": "Instrument de percussion à hauteur déterminée composé de lames d'acier accordées. Frappé avec des baguettes dures ou métalliques, il produit un timbre brillant, pénétrant et campanaire, idéal pour faire ressortir des mélodies aiguës au-dessus de textures orchestrales denses.",
    },
    "Marimba_Concert": {
        "en": "Pitched percussion instrument with wooden bars and resonator tubes beneath each one. Its low register and yarn mallets give it a warm, enveloping tone and allow complex four-mallet harmonies.",
        "fr": "Instrument de percussion à hauteur déterminée composé de lames de bois et de tubes résonateurs sous chacune d'elles. Son registre grave et l'usage de baguettes en fil lui donnent un ton chaud et enveloppant, permettant des harmonies complexes à quatre baguettes.",
    },
    "Piano_CuerdaPercutida_A": {
        "en": "Keyboard instrument with a complex mechanical action in which felt-covered hammers strike the strings. Its design allows extremely precise dynamic response, from forceful percussive attacks to delicate harmonic textures.",
        "fr": "Instrument à clavier doté d'une mécanique complexe où des marteaux recouverts de feutre frappent les cordes. Sa conception permet une réponse dynamique très précise, des attaques percussives puissantes aux textures harmoniques délicates.",
    },
    "Piano_CuerdaPercutida_B": {
        "en": "Variant of the struck-string keyboard family, noted for its integrated acoustic architecture. Its extensive soundboard and escapement mechanism allow it to sustain complex polyphony and project over large orchestral densities.",
        "fr": "Variante de la famille des claviers à cordes frappées, remarquable par son architecture acoustique intégrale. Sa vaste table d'harmonie et son mécanisme d'échappement lui permettent de soutenir des polyphonies complexes et de projeter le son au-dessus de grandes densités orchestrales.",
    },
    "Timbal_Sinfonico_2": {
        "en": "Indispensable complement in the modern orchestral set. Tuned to a different frequency from the main timpani, it extends the performer's tonal range, enabling rapid harmonic changes and sustaining the tonal structure required from Classical to contemporary works.",
        "fr": "Complément indispensable du set orchestral moderne. Accordé à une fréquence différente de celle du timbal principal, il élargit le registre tonal de l'interprète, permettant des changements harmoniques rapides et soutenant la structure tonale exigée du classique au contemporain.",
    },
    "Vibrafono_Pro": {
        "en": "Electroacoustic percussion instrument with aluminum bars and a sustain pedal. It is distinguished by an electric motor that rotates discs inside the resonator tubes, creating its unmistakable vibrato effect.",
        "fr": "Instrument électroacoustique de percussion avec lames d'aluminium et pédale de sustain. Il se distingue par un moteur électrique qui fait tourner des disques dans les tubes résonateurs, produisant son effet de vibrato inimitable.",
    },
    "Viola_ArcoTradicional": {
        "en": "Mid-register bowed string instrument, tuned a fifth lower than the violin. Its dark, warm timbre acts as the harmonic connective tissue between violins and cellos.",
        "fr": "Instrument à cordes frottées au registre intermédiaire, accordé une quinte plus bas que le violon. Son timbre sombre et chaleureux agit comme un tissu harmonique reliant les violons et les violoncelles.",
    },
    "Violin_ArcoTradicional": {
        "en": "Bowed string instrument focused on classical bow technique with horsehair. Sustained, controlled friction on the strings allows mastery of sustain, dynamic phrasing and complex articulations required in chamber and symphonic repertoire.",
        "fr": "Instrument à cordes frottées centré sur la technique classique de l'archet en crin. La friction soutenue et contrôlée sur les cordes permet de maîtriser le sustain, le phrasé dynamique et les articulations complexes du répertoire de chambre et symphonique.",
    },
    "Xilofono_Orquestal": {
        "en": "Percussion instrument made of thick wooden bars tuned chromatically. Struck with hard mallets, it offers a dry, incisive and very short sound, perfect for articulating brilliant rhythmic or melodic passages.",
        "fr": "Instrument de percussion composé de lames de bois épaisses accordées chromatiquement. Frappé avec des baguettes dures, il offre un son sec, incisif et très bref, parfait pour articuler des passages rythmiques ou mélodiques brillants.",
    },
    "mandolina": {
        "en": "Plucked-string instrument of the lute family, with a rounded resonating body and double strings. Its characteristic rapid tremolo technique with plectrum allows continuous melodic notes with great brightness.",
        "fr": "Instrument à cordes pincées de la famille du luth, muni d'une caisse de résonance bombée et de cordes doubles. Sa technique caractéristique de trémolo rapide au plectre permet de soutenir des notes mélodiques continues avec beaucoup de brillance.",
    },
}

def guardar_ontologia():
    """
    Guarda físicamente musica.owl.
    """
    global _onto_instancia

    if _onto_instancia is None:
        return False

    try:
        _onto_instancia.save(file=ruta_ontologia)
        print(f"[OWL] Ontología guardada en: {ruta_ontologia}")
        return True

    except Exception as e:
        print(f"[OWL] Error al guardar ontología: {e}")
        return False


def recargar_ontologia():
    """
    Fuerza la recarga completa de musica.owl.
    """
    global _onto_instancia
    global _serialized_cache

    _onto_instancia = None
    _serialized_cache.clear()

    return cargar_y_razonar()

def expandir_tokens(tokens):
    resultado = []

    for token in tokens:
        agregado = False

        for base, variantes in SYNONYMS.items():
            if token in variantes:
                resultado.extend(variantes)
                agregado = True
                break

        if not agregado:
            resultado.append(token)

    return list(set(resultado))

def cargar_y_razonar():
    """Carga la ontología y ejecuta el razonador HermiT en una ruta segura (una sola vez)."""
    global _onto_instancia
    if _onto_instancia is not None:
        return _onto_instancia
        
    try:
        print("[Motor] Cargando ontología musical por primera vez...")
        onto = get_ontology(f"file://{ruta_ontologia}").load()
        
        carpeta_segura = os.path.abspath(os.path.join(os.path.dirname(__file__), "propio_temp"))
        os.makedirs(carpeta_segura, exist_ok=True)
        
        print("Ejecutando razonador en entorno seguro...")
        try:
            with onto:
                sync_reasoner(infer_property_values=True)
        except Exception as razonador_error:
            print(f"[Motor] Razonador no disponible, continuando con relaciones directas: {razonador_error}")
            
        _onto_instancia = onto
        print("[Motor] ¡Ontología Académica e Inferencias listas en memoria!")
        return _onto_instancia
        
    except Exception as e:
        print(f"Error al inicializar la ontología: {e}")
        return None

# ==========================================
# UTILIDADES DE TEXTO Y TRADUCCIÓN DE DATOS
# ==========================================
def normalize_text(text):
    if text is None: return ""
    text = str(text).lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return " ".join(text.replace("_", " ").replace("-", " ").split())

def normalize_lang(lang):
    if not lang:
        return "es"

    lang = str(lang).lower()
    return lang if lang in SUPPORTED_LANGS else "es"

def detectar_idioma_busqueda(texto, fallback="es"):
    fallback = normalize_lang(fallback)
    texto_original = str(texto or "").lower().strip()
    texto_normalizado = normalize_text(texto)

    if not texto_normalizado:
        return fallback

    tokens = texto_normalizado.split()
    raw_tokens = texto_original.replace("_", " ").replace("-", " ").split()
    scores = {lang: 0 for lang in SUPPORTED_LANGS}

    for token in tokens:
        override_lang = LANGUAGE_EXACT_OVERRIDES.get(token)
        if override_lang:
            scores[override_lang] += 3

    for lang, hints in LANGUAGE_RAW_HINTS.items():
        for hint in hints:
            if hint in texto_original:
                scores[lang] += 4

    for lang, stopwords in LANGUAGE_STOPWORDS.items():
        for token in raw_tokens:
            if token in stopwords:
                scores[lang] += 1

    for lang, hints in LANGUAGE_HINTS.items():
        for token in tokens:
            if token in hints:
                scores[lang] += 2

        for phrase in hints:
            if " " in phrase and phrase in texto_normalizado:
                scores[lang] += 3

    winner, winner_score = max(scores.items(), key=lambda item: item[1])

    if winner_score == 0:
        return fallback

    tied = [lang for lang, score in scores.items() if score == winner_score]

    if "fr" in tied and any(char in texto_original for char in "àâçéèêëîïôûùüÿœ"):
        return "fr"

    if "es" in tied and any(char in texto_original for char in "áéíóúñü"):
        return "es"

    return fallback if fallback in tied else winner

def translate_domain_text(value, lang="es"):
    lang = normalize_lang(lang)

    if value is None or lang == "es":
        return value

    text = str(value)
    translations = DOMAIN_TRANSLATIONS.get(lang, {})

    if text in translations:
        return translations[text]

    translated = text
    for source, target in sorted(translations.items(), key=lambda item: len(item[0]), reverse=True):
        translated = re.sub(re.escape(source), target, translated, flags=re.IGNORECASE)

    return translated

def translate_description(individual_id, description, lang="es"):
    lang = normalize_lang(lang)

    if description is None or lang == "es":
        return description

    text = str(description)
    if text == "-":
        return text

    translated = DESCRIPTION_TRANSLATIONS.get(individual_id, {}).get(lang)
    if translated:
        return translated

    return text

def clean_ontology_name(value):
    if value is None: return "-"
    text = value.name if hasattr(value, "name") else str(value)
    if "#" in text: text = text.split("#")[-1]
    for prefix in PREFIXES_TO_REMOVE:
        text = text.replace(prefix, "")
    return text.replace("_", " ").strip()

def to_bool(value):
    return str(value).lower() in ["true", "1", "si", "sí", "verdadero", "yes"]

def to_int(value):
    try: return int(float(value))
    except: return 0

def get_first_value(individual, property_name, default="-"):
    try:
        valores = getattr(individual, property_name, [])
        return valores[0] if valores else default
    except:
        return default

def get_relation_values(individual, property_names):
    values = []

    for property_name in property_names:
        try:
            values.extend(getattr(individual, property_name, []))
        except:
            pass

    return values

def unique_clean_names(values, lang="es"):
    seen = set()
    cleaned = []

    for value in values:
        name = translate_domain_text(clean_ontology_name(value), lang)
        key = normalize_text(name)

        if name and name != "-" and key not in seen:
            seen.add(key)
            cleaned.append(name)

    return cleaned

def find_related_by_property(target, property_names):
    onto = cargar_y_razonar()
    related = []

    if not onto:
        return related

    for candidate in onto.individuals():
        for value in get_relation_values(candidate, property_names):
            if value == target:
                related.append(candidate)
                break

    return related

# ==========================================
# SERIALIZADOR DE INDIVIDUOS PARA EL FRONTEND
# ==========================================
def serialize_element(ind, lang="es"):
    """Transforma un individuo complejo de Owlready2 en un diccionario plano con caché."""
    lang = normalize_lang(lang)
    cache_key = f"{ind.name}:{lang}"

    if cache_key in _serialized_cache:
        return dict(_serialized_cache[cache_key])

    # Propiedades de datos teóricas e históricas
    nombre = get_first_value(ind, "nombre", ind.name)
    descripcion = get_first_value(ind, "descripcion", "-")
    periodo = get_first_value(ind, "periodoHistorico", "-")       # Ej: Barroco, Romántico
    dificultad = get_first_value(ind, "complejidadTecnica", "-")   # Ej: Alta, Media, Baja
    anio = get_first_value(ind, "anioLanzamiento", "-")            # Año de composición o publicación

    # Relaciones entre objetos
    creador = translate_domain_text(clean_ontology_name(get_first_value(ind, "creadoPor", None)), lang)          # Obras -> Autor
    instrumento = translate_domain_text(clean_ontology_name(get_first_value(ind, "seTocaCon", None)), lang)      # Obras -> Instrumento
    familia = translate_domain_text(clean_ontology_name(get_first_value(ind, "perteneceAFamilia", None)), lang)  # Instrumentos -> Familia técnica

    # Obras compuestas por este individuo. Usa la inversa inferida y un
    # respaldo directo sobre las obras que apuntan al compositor.
    obras_compuestas = unique_clean_names(
        get_relation_values(ind, ["compuso"]) +
        find_related_by_property(ind, ["compuestaPor"]),
        lang
    )

    # Instrumentos que interpretan o requiere esta obra.
    instrumentos_obra = unique_clean_names(
        get_relation_values(ind, ["interpretadaPor", "seTocaCon"]),
        lang
    )

    # Compositor desde data property (para Obras que tienen 'compositor' como string)
    compositor_dp = "-"
    try:
        vals = list(getattr(ind, "compositor", []))
        if vals:
            compositor_dp = translate_domain_text(str(vals[0]), lang)
    except:
        pass

    compositores_relacionados = unique_clean_names(
        get_relation_values(ind, ["compuestaPor", "creadoPor"]),
        lang
    )

    if compositor_dp == "-" and compositores_relacionados:
        compositor_dp = compositores_relacionados[0]

    if creador == "-" and compositores_relacionados:
        creador = compositores_relacionados[0]

    if instrumento == "-" and instrumentos_obra:
        instrumento = instrumentos_obra[0]

    # Mapeo de Tags dinámicos según propiedades booleanas de la ontología
    tags = []
    if to_bool(get_first_value(ind, "esAcustico", False)): tags.append(translate_domain_text("Acústico", lang))
    if to_bool(get_first_value(ind, "requiereAfinacion", False)): tags.append(translate_domain_text("Requiere Afinación", lang))
    if to_bool(get_first_value(ind, "esPolifonica", False)): tags.append(translate_domain_text("Polifónica", lang))

    clases = [
        translate_domain_text(clase.name, lang)
        for clase in ind.is_a
        if hasattr(clase, 'name')
    ]
    for c in clases: 
        if c != "NamedIndividual": tags.append(c)

    data = {
        "id": ind.name,
        "nombre": translate_domain_text(clean_ontology_name(nombre), lang),
        "descripcion": translate_description(ind.name, str(descripcion), lang),
        "periodoHistorico": translate_domain_text(str(periodo), lang),
        "complejidadTecnica": translate_domain_text(str(dificultad), lang),
        "anioLanzamiento": str(anio),
        "autor": creador,
        "instrumentoRequerido": instrumento,
        "familiaInstrumento": familia,
        "clases": clases,
        "tags": tags,
        "obrasCompuestas": obras_compuestas,
        "instrumentosObra": instrumentos_obra,
        "compositorTexto": compositor_dp,
    }
    
    _serialized_cache[cache_key] = data
    return dict(data)

# ==========================================
# CORE DE BÚSQUEDAS Y FILTROS SEMÁNTICOS
# ==========================================
def obtener_clases():
    onto = cargar_y_razonar()
    if not onto: return []
    return [{"nombre": clase.name} for clase in onto.classes()]

def buscar_individuos_por_clase(nombre_clase, lang="es"):
    onto = cargar_y_razonar()
    clase_objeto = onto.search_one(iri=f"*{nombre_clase}") if onto else None
    if not clase_objeto: return []
    return [serialize_element(ind, lang) for ind in clase_objeto.instances()]

def buscar_por_texto(palabra_clave, lang="es"):

    onto = cargar_y_razonar()

    if not onto:
        return []

    tokens = [
        t
        for t in normalize_text(palabra_clave).split()
        if len(t) > 1
    ]

    tokens = expandir_tokens(tokens)

    resultados = []

    for ind in onto.individuals():

        data = serialize_element(ind, lang)

        score = 0

        campos = {
            "nombre": normalize_text(data["nombre"]),
            "autor": normalize_text(data["autor"]),
            "compositor": normalize_text(data["compositorTexto"]),
            "periodo": normalize_text(data["periodoHistorico"]),
            "instrumento": normalize_text(data["instrumentoRequerido"]),
            "instrumentos_obra": normalize_text(" ".join(data["instrumentosObra"])),
            "familia": normalize_text(data["familiaInstrumento"]),
            "obras_compuestas": normalize_text(" ".join(data["obrasCompuestas"])),
            "tags": normalize_text(" ".join(data["tags"]))
        }

        for token in tokens:

            if token in campos["nombre"]:
                score += 20

            if token in campos["autor"]:
                score += 15

            if token in campos["compositor"]:
                score += 15

            if token in campos["obras_compuestas"]:
                score += 12

            if token in campos["familia"]:
                score += 10

            if token in campos["instrumento"]:
                score += 10

            if token in campos["instrumentos_obra"]:
                score += 10

            if token in campos["periodo"]:
                score += 8

            if token in campos["tags"]:
                score += 5

        if score > 0:
            data["score"] = score
            resultados.append(data)

    resultados.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return resultados

def obtener_detalle_individuo(nombre_individuo, lang="es"):
    onto = cargar_y_razonar()
    individuo = onto.search_one(iri=f"*{nombre_individuo}") if onto else None
    if not individuo: return None
    return serialize_element(individuo, lang)

# ==========================================
# ENRUTADOR DE CONSULTAS SEMÁNTICAS HÍBRIDAS
# ==========================================
def q_obras_complejas_piano(lang="es"):
    return [serialize_element(ind, lang) for ind in cargar_y_razonar().individuals() 
            if normalize_text(serialize_element(ind, "es")["complejidadTecnica"]) == "alta" 
            and "piano" in normalize_text(serialize_element(ind, "es")["instrumentoRequerido"])]

def q_autores_periodo_romantico(lang="es"):
    return [serialize_element(ind, lang) for ind in cargar_y_razonar().individuals() 
            if "romantico" in normalize_text(serialize_element(ind, "es")["periodoHistorico"])]

def q_instrumentos_viento_madera(lang="es"):
    return [serialize_element(ind, lang) for ind in cargar_y_razonar().individuals() 
            if "viento madera" in normalize_text(serialize_element(ind, "es")["familiaInstrumento"])]

def q_instrumentos_cuerda(lang="es"):

    return [

        serialize_element(ind, lang)

        for ind in cargar_y_razonar().individuals()

        if "cuerda"
        in normalize_text(
            serialize_element(ind, "es")["familiaInstrumento"]
        )
    ]
def q_instrumentos_viento(lang="es"):

    return [

        serialize_element(ind, lang)

        for ind in cargar_y_razonar().individuals()

        if "viento"
        in normalize_text(
            serialize_element(ind, "es")["familiaInstrumento"]
        )
    ]

def q_instrumentos_percusion(lang="es"):

    return [

        serialize_element(ind, lang)

        for ind in cargar_y_razonar().individuals()

        if "percusion"
        in normalize_text(
            serialize_element(ind, "es")["familiaInstrumento"]
        )
    ]

def q_obras_romanticas(lang="es"):

    return [

        serialize_element(ind, lang)

        for ind in cargar_y_razonar().individuals()

        if "romantico"
        in normalize_text(
            serialize_element(ind, "es")["periodoHistorico"]
        )
    ]

def q_obras_por_autor(param, lang="es"):
    if not param: return []
    p = normalize_text(param)
    return [serialize_element(ind, lang) for ind in cargar_y_razonar().individuals() 
            if p in normalize_text(serialize_element(ind, "es")["autor"])
            or p in normalize_text(serialize_element(ind, "es")["compositorTexto"])]

SEMANTIC_QUERY_MAP = {
    # --- FILTROS POR FAMILIAS DE INSTRUMENTOS (ES / EN / FR) ---
    "instrumentos de cuerda": {"query": "instrumentos_cuerda"},
    "instrumentos de cuerdas": {"query": "instrumentos_cuerda"},
    "string instruments": {"query": "instrumentos_cuerda"},
    "strings": {"query": "instrumentos_cuerda"},
    "instruments a cordes": {"query": "instrumentos_cuerda"},
    "instruments à cordes": {"query": "instrumentos_cuerda"},
    
    "instrumentos de viento": {"query": "instrumentos_viento"},
    "wind instruments": {"query": "instrumentos_viento"},
    "brass instruments": {"query": "instrumentos_viento"},
    "instruments a vent": {"query": "instrumentos_viento"},
    "instruments à vent": {"query": "instrumentos_viento"},
    
    "instrumentos de viento madera": {"query": "instrumentos_viento_madera"},
    "woodwind instruments": {"query": "instrumentos_viento_madera"},
    "woodwinds": {"query": "instrumentos_viento_madera"},
    "instruments a vent en bois": {"query": "instrumentos_viento_madera"},
    "instruments à vent en bois": {"query": "instrumentos_viento_madera"},
    
    "instrumentos de percusion": {"query": "instrumentos_percusion"},
    "instrumentos de percusión": {"query": "instrumentos_percusion"},
    "percussion instruments": {"query": "instrumentos_percusion"},
    "percussion": {"query": "instrumentos_percusion"},
    "instruments de percussion": {"query": "instrumentos_percusion"},
    
    # --- FILTROS POR PERIODO (ES / EN / FR) ---
    "obras romanticas": {"query": "obras_romanticas"},
    "obras románticas": {"query": "obras_romanticas"},
    "romantic works": {"query": "obras_romanticas"},
    "romantic pieces": {"query": "obras_romanticas"},
    "romantic music": {"query": "obras_romanticas"},
    "oeuvres romantiques": {"query": "obras_romanticas"},
    "œuvres romantiques": {"query": "obras_romanticas"},
    
    # =========================================================================
    # --- FILTROS DINÁMICOS POR AUTOR TRILINGÜES (TODOS LOS COMPOSITORES) ---
    # =========================================================================

    # VIVALDI
    "obras de antonio vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},
    "obras de vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},
    "works of antonio vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},
    "works of vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},
    "list of compositions by antonio vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},
    "list of compositions by vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},
    "oeuvres de vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},
    "œuvres de vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},
    "liste des compositions de vivaldi": {"query": "obras_por_autor", "param": "vivaldi"},

    # PIAZZOLLA
    "obras de astor piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},
    "obras de piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},
    "works of astor piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},
    "works of piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},
    "list of compositions by astor piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},
    "list of compositions by piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},
    "oeuvres de piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},
    "œuvres de piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},
    "liste des compositions de piazzolla": {"query": "obras_por_autor", "param": "piazzolla"},

    # LISZT
    "obras de franz liszt": {"query": "obras_por_autor", "param": "liszt"},
    "obras de liszt": {"query": "obras_por_autor", "param": "liszt"},
    "works of franz liszt": {"query": "obras_por_autor", "param": "liszt"},
    "works of liszt": {"query": "obras_por_autor", "param": "liszt"},
    "list of compositions by franz liszt": {"query": "obras_por_autor", "param": "liszt"},
    "list of compositions by liszt": {"query": "obras_por_autor", "param": "liszt"},
    "oeuvres de liszt": {"query": "obras_por_autor", "param": "liszt"},
    "œuvres de liszt": {"query": "obras_por_autor", "param": "liszt"},
    "liste des compositions de liszt": {"query": "obras_por_autor", "param": "liszt"},

    # CHOPIN
    "obras de frederic chopin": {"query": "obras_por_autor", "param": "chopin"},
    "obras de chopin": {"query": "obras_por_autor", "param": "chopin"},
    "works of frederic chopin": {"query": "obras_por_autor", "param": "chopin"},
    "works of chopin": {"query": "obras_por_autor", "param": "chopin"},
    "list of compositions by frederic chopin": {"query": "obras_por_autor", "param": "chopin"},
    "list of compositions by chopin": {"query": "obras_por_autor", "param": "chopin"},
    "oeuvres de chopin": {"query": "obras_por_autor", "param": "chopin"},
    "œuvres de chopin": {"query": "obras_por_autor", "param": "chopin"},
    "liste des compositions de chopin": {"query": "obras_por_autor", "param": "chopin"},

    # JEAN MICHEL JARRE
    "obras de jean michel jarre": {"query": "obras_por_autor", "param": "jarre"},
    "obras de jarre": {"query": "obras_por_autor", "param": "jarre"},
    "works of jean michel jarre": {"query": "obras_por_autor", "param": "jarre"},
    "works of jarre": {"query": "obras_por_autor", "param": "jarre"},
    "list of compositions by jean michel jarre": {"query": "obras_por_autor", "param": "jarre"},
    "list of compositions by jarre": {"query": "obras_por_autor", "param": "jarre"},
    "oeuvres de jarre": {"query": "obras_por_autor", "param": "jarre"},
    "œuvres de jarre": {"query": "obras_por_autor", "param": "jarre"},
    "liste des compositions de jarre": {"query": "obras_por_autor", "param": "jarre"},

    # BACH
    "obras de johann sebastian bach": {"query": "obras_por_autor", "param": "bach"},
    "obras de bach": {"query": "obras_por_autor", "param": "bach"},
    "works of johann sebastian bach": {"query": "obras_por_autor", "param": "bach"},
    "works of bach": {"query": "obras_por_autor", "param": "bach"},
    "list of compositions by johann sebastian bach": {"query": "obras_por_autor", "param": "bach"},
    "list of compositions by bach": {"query": "obras_por_autor", "param": "bach"},
    "oeuvres de bach": {"query": "obras_por_autor", "param": "bach"},
    "œuvres de bach": {"query": "obras_por_autor", "param": "bach"},
    "liste des compositions de bach": {"query": "obras_por_autor", "param": "bach"},

    # BEETHOVEN
    "obras de ludwig van beethoven": {"query": "obras_por_autor", "param": "beethoven"},
    "obras de beethoven": {"query": "obras_por_autor", "param": "beethoven"},
    "works of ludwig van beethoven": {"query": "obras_por_autor", "param": "beethoven"},
    "works of beethoven": {"query": "obras_por_autor", "param": "beethoven"},
    "list of compositions by ludwig van beethoven": {"query": "obras_por_autor", "param": "beethoven"},
    "list of compositions by beethoven": {"query": "obras_por_autor", "param": "beethoven"},
    "oeuvres de beethoven": {"query": "obras_por_autor", "param": "beethoven"},
    "œuvres de beethoven": {"query": "obras_por_autor", "param": "beethoven"},
    "liste des compositions de beethoven": {"query": "obras_por_autor", "param": "beethoven"},

    # PAGANINI
    "obras de niccolo paganini": {"query": "obras_por_autor", "param": "paganini"},
    "obras de paganini": {"query": "obras_por_autor", "param": "paganini"},
    "works of niccolo paganini": {"query": "obras_por_autor", "param": "paganini"},
    "works of paganini": {"query": "obras_por_autor", "param": "paganini"},
    "list of compositions by niccolo paganini": {"query": "obras_por_autor", "param": "paganini"},
    "list of compositions by paganini": {"query": "obras_por_autor", "param": "paganini"},
    "oeuvres de paganini": {"query": "obras_por_autor", "param": "paganini"},
    "œuvres de paganini": {"query": "obras_por_autor", "param": "paganini"},
    "liste des compositions de paganini": {"query": "obras_por_autor", "param": "paganini"},

    # TCHAIKOVSKY
    "obras de pyotr ilyich tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},
    "obras de tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},
    "works of pyotr ilyich tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},
    "works of tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},
    "list of compositions by pyotr ilyich tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},
    "list of compositions by tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},
    "oeuvres de tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},
    "œuvres de tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},
    "liste des compositions de tchaikovsky": {"query": "obras_por_autor", "param": "tchaikovsky"},

    # RACHMANINOFF
    "obras de sergei rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},
    "obras de rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},
    "works of sergei rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},
    "works of rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},
    "list of compositions by sergei rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},
    "list of compositions by rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},
    "oeuvres de rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},
    "œuvres de rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},
    "liste des compositions de rachmaninoff": {"query": "obras_por_autor", "param": "rachmaninoff"},

    # MOZART
    "obras de wolfgang amadeus mozart": {"query": "obras_por_autor", "param": "mozart"},
    "obras de mozart": {"query": "obras_por_autor", "param": "mozart"},
    "works of wolfgang amadeus mozart": {"query": "obras_por_autor", "param": "mozart"},
    "works of mozart": {"query": "obras_por_autor", "param": "mozart"},
    "list of compositions by wolfgang amadeus mozart": {"query": "obras_por_autor", "param": "mozart"},
    "list of compositions by mozart": {"query": "obras_por_autor", "param": "mozart"},
    "oeuvres de mozart": {"query": "obras_por_autor", "param": "mozart"},
    "œuvres de mozart": {"query": "obras_por_autor", "param": "mozart"},
    "liste des compositions de mozart": {"query": "obras_por_autor", "param": "mozart"}
}
def detectar_consulta_semantica(texto):
    texto = normalize_text(texto)

    for frase, info in SEMANTIC_QUERY_MAP.items():
        if normalize_text(frase) in texto:
            return info.get("query"), info.get("param")

    return None, None

def ejecutar_consulta_semantica_musical(query_name, param=None, lang="es"):
    """Router central dinámico para invocar las consultas de lógica técnica."""
    queries = {
        "obras_complejas_piano": q_obras_complejas_piano,
        "autores_periodo_romantico": q_autores_periodo_romantico,
        "instrumentos_viento_madera": q_instrumentos_viento_madera,
        "instrumentos_cuerda": q_instrumentos_cuerda,
        "instrumentos_viento": q_instrumentos_viento,
        "instrumentos_percusion": q_instrumentos_percusion,
        "obras_romanticas": q_obras_romanticas,
    }
    queries_with_param = {
        "obras_por_autor": q_obras_por_autor,
    }

    if query_name in queries: return queries[query_name](lang)
    if query_name in queries_with_param: return queries_with_param[query_name](param, lang)
    return []

# ==========================================
# ÁREA DE PRUEBAS LOCALES
# ==========================================
if __name__ == "__main__":
    termino = "Chopin"
    resultados = buscar_por_texto(termino)
    print(f"\n--- Coincidencias de prueba local para '{termino}': {len(resultados)} ---")
    for r in resultados:
        print(f"-> {r['nombre']} (Autor: {r['autor']} | Tags: {r['tags']})")
