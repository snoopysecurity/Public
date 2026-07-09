#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import re
import sys
from typing import Dict, List, Optional

import requests


class CommitSearch:
    BASE_URL = "https://chromium.googlesource.com"

    PRODUCTS = {
        "chromium": {
            "log_path": "/chromium/src/+log/",
            "commit_path": "/chromium/src/+/",
        },
        "v8": {
            "log_path": "/v8/v8/+log/",
            "commit_path": "/v8/v8/+/",
        },
    }

    BUG_FIELD_RE = re.compile(
        r"(?im)^(bug|bugs|fixed|fixes):\s*(.+)$"
    )

    BUG_ID_RE = re.compile(r"\b\d+\b")

    def __init__(self, product: str, version: str, bug_id: str, max_pages: int = 500):
        if product not in self.PRODUCTS:
            raise ValueError(f'Unsupported product "{product}". Use "chromium" or "v8".')

        self.product = product
        self.version = version
        self.bug_id = str(bug_id)
        self.max_pages = max_pages

        paths = self.PRODUCTS[product]
        self.log_url = self.BASE_URL + paths["log_path"] + version
        self.commit_url = self.BASE_URL + paths["commit_path"]

        self.session = requests.Session()

    def _fetch_json(self, url: str) -> Optional[Dict]:
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            content = response.text

            # googlesource JSON usually starts with XSSI protection:
            # )]}'
            if content.startswith(")]}'"):
                content = content[4:]

            return json.loads(content)

        except requests.RequestException as error:
            print(f"[-] Request failed: {error}", file=sys.stderr)
            return None

        except json.JSONDecodeError:
            print(f"[-] Failed to decode JSON from: {url}", file=sys.stderr)
            return None

    def _message_mentions_bug(self, message: str) -> bool:
        """
        Checks commit message footers such as:

        Bug: 123456
        Bugs: chromium:123456, v8:98765
        Fixed: 123456
        Fixes: crbug.com/123456
        """
        matches = self.BUG_FIELD_RE.findall(message)

        for _, bug_text in matches:
            ids = self.BUG_ID_RE.findall(bug_text)

            if self.bug_id in ids:
                return True

        return False

    def find_bug_commits(self) -> List[str]:
        commits: List[str] = []
        seen = set()

        url = self.log_url + "/?format=JSON"

        for _ in range(self.max_pages):
            log = self._fetch_json(url)

            if not log:
                break

            for commit in log.get("log", []):
                message = commit.get("message", "")
                sha1 = commit.get("commit")

                if not sha1:
                    continue

                if self._message_mentions_bug(message):
                    commit_link = self.commit_url + sha1

                    if commit_link not in seen:
                        commits.append(commit_link)
                        seen.add(commit_link)

            next_id = log.get("next")

            if not next_id:
                break

            url = f"{self.log_url}?s={next_id}&format=JSON"

        return commits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search Chromium or V8 release logs for commits linked to a bug ID."
    )

    parser.add_argument(
        "-b",
        "--bug",
        required=True,
        help="Bug ID from Chromium issue tracker or release report.",
    )

    parser.add_argument(
        "-r",
        "--rel",
        required=True,
        help="Release version, branch, tag, or revision range accepted by googlesource.",
    )

    parser.add_argument(
        "-p",
        "--prod",
        default="chromium",
        choices=["chromium", "v8"],
        help='Product to search. Default: "chromium".',
    )

    parser.add_argument(
        "-mp",
        "--maxpages",
        type=int,
        default=500,
        help="Maximum number of log pages to search. Default: 500.",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON.",
    )

    args = parser.parse_args()

    if args.maxpages <= 0:
        print("[-] --maxpages must be greater than 0", file=sys.stderr)
        return 2

    search = CommitSearch(
        product=args.prod,
        version=args.rel,
        bug_id=args.bug,
        max_pages=args.maxpages,
    )

    commits = search.find_bug_commits()

    if args.json:
        print(json.dumps({"bug": args.bug, "commits": commits}, indent=2))
        return 0 if commits else 1

    if not commits:
        print("[-] Nothing was found")
        return 1

    print("[+] Commit found:")

    for commit in commits:
        print(commit)

    return 0


if __name__ == "__main__":
    sys.exit(main())
