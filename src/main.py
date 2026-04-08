import sys
import os

from src.io.parser import parse_input_bytes
from src.controller.scheduler import run_scheduling
from src.io.layoutOutput import buildReport


def main() -> None:
    # 1. Xác định đường dẫn file input và output
    if len(sys.argv) >= 3:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
    elif len(sys.argv) == 2:
        input_path = sys.argv[1]
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_path = os.path.join(base_dir, "public", "output.txt")
    else:
        # Fallback: tìm public/input.txt và public/output.txt tương đối với thư mục chạy lệnh
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        input_path = os.path.join(base_dir, "public", "input.txt")
        output_path = os.path.join(base_dir, "public", "output.txt")

    if not os.path.isfile(input_path):
        print(f"[ERROR] File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # 2. Parse input
    try:
        with open(input_path, "rb") as f:
            queues, processes = parse_input_bytes(f.read())
    except ValueError as e:
        print(f"[ERROR] Invalid input: {e}", file=sys.stderr)
        sys.exit(1)

    if not processes:
        print("[WARNING] No processes found in input file. Nothing to schedule.")
        return

    segments, processes = run_scheduling(queues, processes)
    report = buildReport(segments, processes)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)


if __name__ == "__main__":
    main()
