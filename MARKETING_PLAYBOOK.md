# BRIDGE Commercialization Playbook

## Value proposition
- Turnkey sync between WooCommerce and SoftOne Capital ERP: price/discount alignment, unmatched-product handling, analytics, and safety prompts.
- Reduces manual data entry and pricing errors while giving merchants a single source of truth.

## Target customers
- Mid-size WooCommerce merchants using SoftOne Capital ERP who struggle with price and product consistency across channels.
- Agencies managing multiple WooCommerce stores that want a repeatable sync solution.
- IT partners/integrators serving Greek and EU merchants running Capital ERP.

## Market sizing (directional)
- WooCommerce powers millions of online stores; public ecosystem trackers commonly cite **6–7 million** WooCommerce sites worldwide.
- ERP-connected merchants are a smaller slice but still a sizable niche: thousands of mid-market stores in EU markets run WooCommerce with external ERPs and need automated sync for price/stock accuracy.
- Position BRIDGE as the specialized choice for the WooCommerce + SoftOne Capital pairing rather than a generic connector.

## Monetization models
- **SaaS/hosted**: Managed Windows host or packaged VM; price per store/company or order volume; bundle monitoring/alerts as premium.
- **Per-seat/company license**: Perpetual or annual with maintenance; volume discounts for agencies.
- **Services**: Paid onboarding, SKU mapping, initial full sync, and periodic health checks.
- **Add-on features**: Scheduled syncs, Excel exports, image management, advanced analytics, and multi-store support.

## Packaging & distribution
- **Windows installer/portable build** with bundled Python and dependencies; add first-run wizard for credentials and license key.
- **Auto-update channel**: app checks a signed manifest on your server; admins publish new builds + manifests (see `tools/prepare_release.py`).
- **Licensing**: issue license keys per customer; validate on launch and during update checks.
- **Support assets**: quick-start guide, troubleshooting script, and in-app log export to reduce support effort.

## WooCommerce plugin channel
- You can list a **companion plugin** on the WooCommerce marketplace to handle site-side webhook/endpoints and point buyers to the desktop app license.
- Marketplace rules typically require clear pricing, support policy, and update delivery via the WooCommerce update system; for the desktop app, keep updates in your own channel while the plugin updates through WooCommerce.
- Use the plugin listing to capture leads and provide a lightweight connector that talks to the BRIDGE desktop service.

## Go-to-market steps
1) **Productize onboarding**: wizard for API keys, connectivity tests, SKU matching mode, and license entry.
2) **Pilot with 3–5 merchants**: validate stability, collect testimonials, and refine health checks.
3) **Publish pricing tiers**: Starter/Pro/Enterprise based on stores/products/sync frequency; include support SLAs.
4) **Launch update pipeline**: host signed manifests + builds; document admin steps to push updates and operators steps to fetch them.
5) **Agency program**: white-label option, volume licensing, and training for agency staff.
6) **Content + demos**: short video showing price sync, unmatched handling, and analytics; offer a time-limited trial build.

## Admin update delivery (desktop app)
- Prepare a new build and run `python tools/prepare_release.py --version <X.Y.Z> --manifest-url <https://yourdomain/updates/manifest.json> --artifact-url <https://yourdomain/updates/bridge_<X.Y.Z>.zip>`.
- Upload the generated manifest and build artifact to your update server (HTTPS).
- Operators with internet access will see the new version via the in-app update check and can download/apply it automatically.
- For offline sites, send the build via USB/shared drive and provide the license key; the app should allow manual update import.

## Sales assets to maximize potential
- ROI calculator (time saved, reduction in price mismatches) and case studies from pilot merchants.
- Security note: Capital ERP remains the source of truth; WooCommerce updates are scoped to prices/discounts, reducing risk.
- Support tiers with guaranteed response times and periodic sync-audits.

