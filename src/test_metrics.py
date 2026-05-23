from quality_metrics import *

result = evaluate_video(
    "data/raw/test.mp4",
    "data/hevc/test_hevc.mp4",
    "data/vvc/test_vvc.mp4"
)

for key, value in result.items():
    print(key, ":", value)