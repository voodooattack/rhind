"""Run every proof in this directory, in sorted order."""

from pathlib import Path

from proofs._discover import run_proofs


def main():
    run_proofs("proofs", Path(__file__).parent)


if __name__ == "__main__":
    main()
