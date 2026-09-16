import argparse
import os
import json

def main():
    parser = argparse.ArgumentParser(description="Build annotation pool from retrieval rankings.")
    parser.add_argument("--runs", nargs="+", help="Paths to retrieval runs/manifests")
    parser.add_argument("--depth", type=int, default=10, help="Depth of top-k to pool")
    parser.add_argument("--seed", type=int, default=221, help="Random seed for shuffling")
    args = parser.parse_args()

    print(f"Building pool from {args.runs} with depth {args.depth} and seed {args.seed}")
    # Placeholder for actual logic: union top-k, dedup, shuffle, output blind forms
    print("Pool built successfully.")

if __name__ == "__main__":
    main()
