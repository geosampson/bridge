# BRIDGE Productized Distribution

This folder contains a self-contained, commercial-ready packaging of BRIDGE with
licensing, onboarding, and update delivery hooks. It is designed to be copied as
its own repository when distributing to customers.

## Highlights
- Guided setup wizard for WooCommerce + ERP credentials and license activation.
- License enforcement using signed tokens and offline-friendly validation.
- Background update checker that pulls new builds when an internet connection is
  available.
- Admin tooling to publish updates via a signed manifest file.

## Quick start (operator)
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the setup wizard to capture credentials and the license key:
   ```bash
   python -m bridge_productized.setup_wizard --license YOUR-LICENSE-KEY
   ```
3. Launch the productized BRIDGE entry point:
   ```bash
   python -m bridge_productized.main
   ```

## Delivering updates (admin)
1. Build or zip the new application version and upload it somewhere reachable by
   customers (for example, `https://updates.example.com/bridge/v3.0/build.zip`).
2. Generate a manifest that points to the new download and sign it:
   ```bash
   BRIDGE_LICENSE_SECRET="your-signing-secret" \
   python tools/prepare_release.py \
     --version 3.0.0 \
     --download-url https://updates.example.com/bridge/v3.0/build.zip \
     --notes "Price sync scheduler + improved onboarding"
   ```
   The command produces `productized_bridge/public_manifest.json`; host this
   file at the URL configured in `bridge_productized.update_service.DEFAULT_MANIFEST_URL`.
3. When customer machines are online, the app checks the manifest at startup and
   prompts the user if a newer version is available. The downloaded archive is
   saved next to the config directory for manual or scripted installation.

## Issuing customer licenses
- Set the signing secret in `BRIDGE_LICENSE_SECRET` and run:
  ```bash
  python tools/prepare_release.py --issue-license "Customer Name" --expires 2025-12-31
  ```
- Share the generated license key with the customer; they paste it into the
  setup wizard or the existing configuration file.

## Scope
The code in `bridge_productized/` does not change the legacy `bridge_app.py`
implementation; it wraps configuration, licensing, and update distribution
around the existing application so it can be commercialized safely.
