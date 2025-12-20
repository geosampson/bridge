from __future__ import annotations

import argparse
from getpass import getpass

from .config import BridgeConfig, create_config


def prompt_if_missing(value: str | None, label: str, secret: bool = False) -> str:
    if value:
        return value
    prompt = f"Enter {label}: "
    return getpass(prompt) if secret else input(prompt).strip()


def run_setup_wizard() -> BridgeConfig:
    parser = argparse.ArgumentParser(description="Configure BRIDGE credentials and licensing")
    parser.add_argument("--store-url")
    parser.add_argument("--consumer-key")
    parser.add_argument("--consumer-secret")
    parser.add_argument("--capital-base-url")
    parser.add_argument("--capital-username")
    parser.add_argument("--capital-password")
    parser.add_argument("--capital-company", type=int)
    parser.add_argument("--capital-fiscalyear", type=int)
    parser.add_argument("--capital-branch", type=int)
    parser.add_argument("--license")
    parser.add_argument("--customer-name")
    parser.add_argument("--update-channel", default="stable")
    parser.add_argument("--current-version", default="0.0.0")
    args = parser.parse_args()

    store_url = prompt_if_missing(args.store_url, "WooCommerce store URL")
    consumer_key = prompt_if_missing(args.consumer_key, "WooCommerce consumer key")
    consumer_secret = prompt_if_missing(args.consumer_secret, "WooCommerce consumer secret", secret=True)
    capital_base_url = prompt_if_missing(args.capital_base_url, "Capital ERP base URL")
    capital_username = prompt_if_missing(args.capital_username, "Capital ERP username")
    capital_password = prompt_if_missing(args.capital_password, "Capital ERP password", secret=True)
    capital_company = args.capital_company or int(prompt_if_missing(None, "Capital ERP company ID"))
    capital_fiscalyear = args.capital_fiscalyear or int(prompt_if_missing(None, "Capital ERP fiscal year"))
    capital_branch = args.capital_branch or int(prompt_if_missing(None, "Capital ERP branch"))
    license_key = prompt_if_missing(args.license, "license key")
    customer_name = prompt_if_missing(args.customer_name, "customer name")

    config = create_config(
        store_url=store_url,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        capital_base_url=capital_base_url,
        capital_username=capital_username,
        capital_password=capital_password,
        capital_company=capital_company,
        capital_fiscalyear=capital_fiscalyear,
        capital_branch=capital_branch,
        license_key=license_key,
        customer_name=customer_name,
        update_channel=args.update_channel,
        current_version=args.current_version,
    )
    print(f"Configuration saved to {config}")
    return config


if __name__ == "__main__":
    run_setup_wizard()
