# import sys
# import os

# from src.io.parser import parse_input
# from src.controller.scheduler import run_scheduling
# from src.io.layoutOutput import buildReport


# def main() -> None:
#     # 1. Xác định đường dẫn file input
#     if len(sys.argv) >= 2:
#         input_path = sys.argv[1]
#     else:
#         # Fallback: tìm public/input.txt tương đối với thư mục chạy lệnh
#         base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#         input_path = os.path.join(base_dir, "public", "input.txt")

#     if not os.path.isfile(input_path):
#         print(f"[ERROR] File not found: {input_path}", file=sys.stderr)
#         sys.exit(1)

#     # 2. Parse input
#     try:
#         queues, processes = parse_input(input_path)
#     except ValueError as e:
#         print(f"[ERROR] Invalid input: {e}", file=sys.stderr)
#         sys.exit(1)

#     if not processes:
#         print("[WARNING] No processes found in input file. Nothing to schedule.")
#         return

#     segments, processes = run_scheduling(queues, processes)
#     print(buildReport(segments, processes))


# if __name__ == "__main__":
#     main()
