"""Preview the seed, or apply only to an explicitly selected loopback DynamoDB."""

import argparse
import json
from urllib.parse import urlsplit

import boto3

from common.templates.repository import TemplateRepository
from common.templates.seed import SUPPLIER_ONBOARDING


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint-url", help="Local DynamoDB URL; omitted means preview only.")
    parser.add_argument("--table", default="docflow-dev")
    args = parser.parse_args()
    if not args.endpoint_url:
        print(json.dumps(SUPPLIER_ONBOARDING.content(), indent=2))
        return
    url = urlsplit(args.endpoint_url)
    if (
        url.scheme != "http"
        or url.hostname not in {"localhost", "127.0.0.1", "::1"}
        or url.username
        or url.password
        or url.query
        or url.fragment
        or url.path not in {"", "/"}
    ):
        parser.error(
            "Only an explicit HTTP loopback endpoint is supported; AWS deployment is deferred."
        )
    client = boto3.client(
        "dynamodb",
        region_name="us-east-1",
        endpoint_url=args.endpoint_url,
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )
    created = TemplateRepository(client, args.table).publish(
        SUPPLIER_ONBOARDING, actor_id="local-seed"
    )
    print("PASS: template created" if created else "PASS: template already matches")


if __name__ == "__main__":
    main()
