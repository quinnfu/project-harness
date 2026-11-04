# Pattern: web application

Signals: frontend framework dependencies (React/Vue/Svelte/Next…), `index.html`, `vite.config.*`, a backend service entry point, `docker-compose*.yml`, `.env.example`.

- **Q1**: the architecture doc covers the frontend/backend boundary, where routes/pages live, data flow, external services.
- **Q2**: unit tests mostly follow standard conventions; what usually needs writing: how to start locally (ports, required services, where `.env` comes from), end-to-end/browser verification, which changes must actually be looked at in a browser. For UI changes, "Definition of done" should include an end-to-end test or opening the page to confirm.
- **Q3**: requirements are often described as pages/user flows; suggest organizing requirement docs by user flow.
- **Q4**: common key rules — never commit secrets (document variable names in `.env.example`), API contracts, design-system/component reuse conventions.
- **Q6**: focus on whether the environment variable list matches the code and whether startup instructions still work.
