# Repo Conventions

- `web/` is a Vite React + TypeScript app.
- Route shell logic lives in `web/src/components/shell/`.
- Feature pages live in `web/src/features/{dashboard,orders,customers,settings}/`.
- Reusable design-system components live in `web/src/components/ui/`.
- Orders should keep using `web/src/lib/api/orders.ts`; do not add direct `fetch` calls.
- Keep tests colocated as `*.test.tsx`; benchmark validators use `*.benchmark.test.tsx`.
