# la-vie-en-rose

*Walking every street of Paris — and building the web app that chronicles,
maps, and proves it.*

I live in Paris and I'm on a mission to walk all of it: every rue, avenue,
passage, impasse, villa, and park path. More than 6,000 named streets. This
repository is the home of the web app built around that mission.

## What it does

- **The map** — the street network of Paris, showing what's been walked and
  what remains, rendered as a living map that updates itself after every walk.
- **The chronicle** — every walk as a named entry: stats, trace, story, and
  whether the kids came along.
- **Proof of Walk** — every walk anchored as a public, tamper-proof
  attestation on a blockchain, verifiable by anyone.
- **For walkers** — curated routes, recommendations, and practical layers to
  discover Paris on foot. (Coming as the mission progresses.)

The site is available in English and French.

## How it works

Apple Watch → Strava → webhook → ingestion worker → map-matching against the
Paris street network (PostgreSQL + PostGIS) → coverage & chronicle updates →
Proof of Walk anchoring. Backend: Python + FastAPI. Frontend: Next.js +
MapLibre GL. Hosted on Fly.io, in Paris.

Full vision and architecture: [PROJECT.md](./PROJECT.md).
Working conventions for development: [CLAUDE.md](./CLAUDE.md).

## Data & attribution

Street and place data © [OpenStreetMap](https://www.openstreetmap.org/copyright)
contributors and [Paris Open Data](https://opendata.paris.fr/) (ODbL).

## License

Code is licensed under the [MIT License](./LICENSE). Photos, texts, and other
site content are not covered by the code license.
