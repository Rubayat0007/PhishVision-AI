from pathlib import Path
from PIL import Image
import numpy as np

root = Path("data/clean_split_v2")

results = []

for path in sorted(root.rglob("*.jpg")):
    with Image.open(path) as image:
        array = np.asarray(image.convert("L"), dtype=np.float32)

    mean = float(array.mean())
    std = float(array.std())

    results.append({
        "path": str(path.relative_to(root)),
        "mean": mean,
        "std": std,
    })

stds = np.array([r["std"] for r in results])
means = np.array([r["mean"] for r in results])

print(f"Total images: {len(results)}")
print(f"Mean brightness: {means.mean():.2f}")
print(f"Brightness range: {means.min():.2f} - {means.max():.2f}")
print(f"Mean pixel std: {stds.mean():.2f}")
print(f"Pixel std range: {stds.min():.2f} - {stds.max():.2f}")

uniform = [r for r in results if r["std"] < 5.0]

print(f"Near-uniform images (pixel std < 5): {len(uniform)}")

if uniform:
    print()
    print("===== NEAR-UNIFORM IMAGES =====")
    for item in uniform:
        print(
            f'{item["path"]} '
            f'mean={item["mean"]:.2f} '
            f'std={item["std"]:.2f}'
        )
