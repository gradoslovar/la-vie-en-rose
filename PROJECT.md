# la-vie-en-rose - Every Street of Paris

> I live in Paris, and I am walking all of it. Every street, every passage,
> every impasse, every park path. This is the story of that mission - and of
> the web app I'm building around it.

---

## 1. The Mission

I'm on a mission to walk every street in Paris. Literally every one: the grand
avenues and the dead-end impasses, the covered passages and the villas hidden
behind gates, the park alleys where the city breathes. When it's done, I will
have covered more than 1,700 kilometers of unique streets - and far more than
that in reality, because streets repeat, connectors get re-walked, and every
impasse costs double by definition. The final number might be 3,000 km. I
don't care.

Because this is not about efficiency. I have no tactics, no route plan, no
deadline. Inspiration decides, and daily life decides - I'm a single dad with
two kids, and sometimes that's the main driver of what I can do and whether I
can do it at all. Some of my walks happen with my kids, and those are marked
"With Kid" - they are covering their own Paris inside mine, one small-hand walk
at a time. Years from now, that layer of the map will mean more to me than any
statistic.

I'm not here to complete a checklist. I'm here to make the ride, enjoy the
ride, and build a fun and cool project around it.

## 2. What I'm Building

A public website dedicated to this mission - and, through it, to Paris itself.

The world can watch: the map, the progress, the chronicle of walks, the
proofs, and eventually the photos and my recommendations. Writing, on the
other hand, is done by exactly one person - me - mostly with my feet. There's
a single admin account, mine, connected to my Strava.

For now there is no user system and no multi-tenancy. This is a deliberate
simplification, and today I see no reason to change it - but this document
doesn't do dogma. If life or inspiration one day makes a case for other
walkers having a home here, we'll rethink it then.

The site is available in English and French, from the start.

### My app is the source of truth - not the GPS

GPS in Paris drifts. Haussmann canyons, narrow passages, covered galleries -
my traces sometimes walk me "through buildings," miss streets I genuinely
walked, or credit streets I never touched. Tools like CityStrides are slaves
to the trace. My app is not. Automatic matching will do the heavy lifting, but
I keep the final word: admin tooling lets me mark a street as truly walked
when the satellite lied, or reject a false positive. Human truth over
satellite truth. In my app, I fix all of this.

## 3. How the Data Flows

My equipment is simply what I have and use:

- **Apple Watch** records the outdoor walk workout.
- **Strava** receives it - that's my social layer, and it gives shape and form
  to each walking tour. Every mission walk is named with a `pa-` prefix - `pa`
  simply means Paris, and the prefix is how mission walks are identified
  (and how generic Strava names are avoided). Sometimes a name refers to what
  the walk was made for (`pa-sardines`), but that's not a rule and not
  important.
- **"With Kid"** is a Strava tag I apply to walks made with my kids, so they
  can be found by tag later. It matters: in the app it becomes a filter and a
  layer of memories.
- **CityStrides** stays connected as a casual reference - a quick "what's
  going on" map - but it plays no role in this system.

The pipeline:

```
Apple Watch (Outdoor Walk)
        │
        ▼
Strava  ← activity named "pa-…", "With Kid" when applicable
        │
        ▼  Strava webhook (activity created/updated)
Ingestion worker
        │  1. Fetch activity + GPS stream via Strava API (filter: "pa-" prefix)
        │  2. Map-match the trace against the Paris street network (PostGIS)
        │  3. Update segment coverage, stats, and the chronicle
        │  4. Async: Proof of Walk (see below)
        ▼
PostgreSQL + PostGIS  ──►  Vector tiles  ──►  MapLibre GL map on the site
```

The magic moment I'm building toward: I finish a walk somewhere in Paris, and
minutes later the site has updated itself and anchored the proof. No manual
steps.

A walk in my app is never an anonymous trace. It's a chronicle entry: a name,
a date, a distance, steps, duration, whether the kids were along, a story if
there is one, photos if I took them.

## 4. Proof of Walk

"Proof of Walk" is my invention - a wink at proof-of-work and proof-of-stake.
It's not a consensus mechanism; it's a public, tamper-proof, timestamped
attestation of the mission. Once a walk is anchored, nobody - including
future me - can quietly edit history. The mission becomes auditable, and
anyone can check every segment of it. I'm doing this for fun, for involving
more tech in the project, and because it fits the spirit of the quest: the
whole point is that it's real.

The pattern I've chosen:

- The full trace file lives in permanent storage. **Arweave** is the current
  placeholder (pay once, stored effectively forever); IPFS is the alternative.
  Not written in stone - to be discussed in detail when the time comes.
- On-chain goes only a small attestation: the SHA-256 hash of the file, the
  storage pointer, the date, distance, covered street IDs. Cost per walk:
  negligible.
- A possible elegance: a **Merkle tree of all walks**, with a single on-chain
  root committing to the entire mission history, and compact inclusion proofs
  per walk. Very "proof of walk" in flavor.
- Chain choice is still open - Solana, or an Ethereum L2 (Base/Arbitrum,
  possibly via EAS, the Ethereum Attestation Service). I have no preference
  yet; we decide at implementation.

One thing I'll state transparently on the site itself: the chain proves the
*data* existed at a moment in time and was never altered - it cannot prove my
legs did the walking. What completes the proof is the human layer: a public
Strava account, heart-rate data from the watch, photos, and the sheer
consistency of hundreds of walks. Saying this openly makes the project more
credible, not less.

Ideas I'm keeping warm: every street segment on the map linking to its
attestation; a "verify this walk" button that re-hashes the file live in the
browser; milestone badges. I'm open to more blockchain use cases along the
way - I'm totally into making it interactive.

## 5. The Stack

| Layer          | Choice                                              |
|----------------|-----------------------------------------------------|
| Language       | **TypeScript everywhere**, strict mode              |
| Frontend       | **Next.js** (React)                                 |
| Map            | **MapLibre GL JS** + vector tiles                   |
| Database       | **PostgreSQL + PostGIS** - the geospatial brain     |
| Ingestion      | Worker process (webhook-driven, async jobs)         |
| Chain          | Open: Solana or EVM L2; Arweave as storage placeholder |
| Hosting        | **Fly.io** (decided) - CDG region, physically in Paris |
| Repo           | **GitHub monorepo**: app, worker, infra, chain package |
| CI/CD          | GitHub Actions: typecheck, lint, test, preview deploys on PRs, deploy on merge |
| Infra          | As code (fly.toml / Terraform or Bicep), Dependabot, branch protection |

Everything lives on GitHub with tooling like every real app: top-notch
stack, proper CI/CD.

Build order and working conventions live in `CLAUDE.md`.

## 6. Features

### The core (v1)
- The public map of Paris: the street network with walked/unwalked state, and
  my progress toward 100%.
- The chronicle: every `pa-` walk as an entry - name, stats, trace, story,
  with-kid flag.
- Stats that celebrate the ride, never score it: segment-based completion %
  as the headline; total distance walked vs. unique distance completed (the
  "overhead ratio" - I walked the city 2.4 times to finish it once - as fun
  trivia); per-arrondissement breakdowns.
- Fully automatic ingestion from the Strava webhook.
- Admin: my single Strava-connected account, plus the correction tooling that
  makes me - not the GPS - the source of truth.
- Proof of Walk anchoring and a public verification page.
- English and French.

### Where it grows next (my stated wishes)
- **Recommendations**: bars, restaurants and similar places discovered along
  the way, with descriptions and photos. The recommendations of someone who
  walked *everything* - an authority no tourism site can fake.
- **Photo gallery**: photos I take along the way, browsable by visitors.
- **Curated routes**: public Strava segments I design as invitations to meet
  Paris by walking - something like 10 kilometers, 3 arrondissements, this
  and that along the way to make a stop, grab something.
- The kids' layer: the sub-map of streets we've walked together.
- **Practical layers for walkers**, from Paris open data: public toilets,
  drinking fountains, cool spots (îlots de fraîcheur), possibly street
  parking. Optional map layers, and shown along curated routes and
  recommendations - useful public spots along the way. Fun and useful.
- More blockchain interactivity - badges, milestones, experiments. Open.

## 7. The Denominator (decided)

"Every street of Paris" means, in my definition:

- **All named streets of Paris** - the official nomenclature counts more than
  6,000 voies: rues, avenues, boulevards, passages, impasses, villas, cités,
  places, quais.
- **Including the streets that lie outside the périphérique** but belong to
  Paris - they are part of the mission.
- **Excluding the Bois de Boulogne and the Bois de Vincennes.** Administratively
  Paris, but forests are not part of my project. Not included, full stop.
- **Parks are in** - I walk parks, not only streets. Park paths and cemetery
  alleys (Père-Lachaise has a real street network of its own) are covered on a
  best-effort basis: if some path can't be cleanly tracked, no big deal. This
  is fun; I'm not losing my mind over every inch. Everything I walk remains
  visible in my Strava workouts anyway.

**Data sources (decided): a hybrid, with me as final editor.**

- **OpenStreetMap** provides the geometric backbone: the fresh, continuously
  updated walkable network - streets, passages, park paths - imported into
  PostGIS as segments. To be clear: OSM the *data*, not OSM the *map*. Its
  default rendering is average; ours will not be. We take only the geometry
  and render it ourselves in MapLibre with a signature style. The beauty is
  entirely in our hands.
- **Paris open data** (`denominations-emprises-voies-actuelles`) provides the
  authoritative registry of named voies plus metadata: arrondissement,
  quartier, and - a treasure - the history and origin of each street name.
  Every street page on the site can tell the story of its name, from official
  sources. (The city's `troncon_voie` centerline dataset has the perfect
  segment model but was last updated in June 2018 - too stale to be the
  backbone; useful at most as a cross-check.)
- Both sources are ODbL-licensed; attribution is straightforward.
- Where sources disagree, or at the edges (a courtyard, a cemetery alley),
  **I decide**. Same philosophy as the GPS corrections: I am the source of
  truth here too.

## 8. Open Questions (tracked, not blocking)

1. **Chain choice.** Solana vs. EVM L2 (and whether EAS fits). Permanent
   storage (Arweave vs. IPFS vs. other) is part of the same discussion.
2. **Photos.** Storage and pipeline (likely object storage + optimization);
   decide together with the gallery feature.
3. **Map-matching specifics.** Buffer-based PostGIS matching vs. proper HMM
   map-matching (Valhalla/OSRM); decide during the build.

## 9. Vocabulary

- **Proof of Walk** - my attestation concept: publicly verifiable,
  tamper-proof evidence of the mission's record.
- **`pa-`** - the prefix marking my mission walks on Strava.
- **With Kid** - walks done with my children.
- **The chronicle** - the sequence of named walks that *is* the mission, as
  opposed to a pile of GPS traces.
- **The overhead ratio** - total km walked vs. unique km completed. Trivia,
  never a score.