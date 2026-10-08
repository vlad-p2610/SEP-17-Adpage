"""Run the complete synthetic profiling demonstration without database access.

From the repository root: python -m examples.data_analysis.run_demo
"""
import argparse
import json
from pathlib import Path

import yaml

from examples.data_analysis.generate_demo import demo_data
from src.data_analysis import AnalysisSchema, profile_dataframe, render_markdown


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("analysis-output/demo"))
    args = parser.parse_args()
    schema = AnalysisSchema(**yaml.safe_load(Path(__file__).with_name("schema.yaml").read_text()))
    df = demo_data()
    report = profile_dataframe(df, schema, include_record_findings=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_dir / "synthetic_input.csv", index=False)
    (args.output_dir / "profile.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    (args.output_dir / "profile.md").write_text(render_markdown(report))
    print(f"SYNTHETIC DATA ONLY: {report['rows']} rows, {report['candidate_rows']} candidate rows.")
    print(f"{report['invalid_value_rows']} invalid-value rows; {report['duplicate_key_rows']} duplicate-key rows.")
    print(f"Review {args.output_dir / 'profile.md'} and {args.output_dir / 'profile.json'}.")


if __name__ == "__main__":
    main()
