import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = (
    PROJECT_ROOT
    / "results"
    / "adversarial_robustness.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "results"
    / "robustness_plots"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def load_results():
    rows = []

    with CSV_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append(
                {
                    "attack": row["attack"],
                    "epsilon": float(row["epsilon"]),
                    "clean_probability": float(
                        row["clean_phishing_probability"]
                    ),
                    "adversarial_probability": float(
                        row["adversarial_phishing_probability"]
                    ),
                    "successful_flip": int(
                        row["successful_flip"]
                    ),
                }
            )

    return rows


def aggregate(rows):
    attacks = ["FGSM", "PGD"]

    data = {}

    for attack in attacks:
        attack_rows = [
            row
            for row in rows
            if row["attack"] == attack
        ]

        epsilons = sorted(
            set(row["epsilon"] for row in attack_rows)
        )

        attack_data = {
            "epsilon": [],
            "asr": [],
            "probability": [],
            "recall": [],
        }

        for epsilon in epsilons:
            matching = [
                row
                for row in attack_rows
                if row["epsilon"] == epsilon
            ]

            total = len(matching)

            successful = sum(
                row["successful_flip"]
                for row in matching
            )

            asr = successful / total

            probability = sum(
                row["adversarial_probability"]
                for row in matching
            ) / total

            recall = 1.0 - asr

            attack_data["epsilon"].append(epsilon)
            attack_data["asr"].append(asr)
            attack_data["probability"].append(probability)
            attack_data["recall"].append(recall)

        data[attack] = attack_data

    clean_probability = sum(
        row["clean_probability"]
        for row in rows
    ) / len(rows)

    return data, clean_probability


def plot_attack_success_rate(data):
    plt.figure()

    for attack in ["FGSM", "PGD"]:
        plt.plot(
            data[attack]["epsilon"],
            data[attack]["asr"],
            marker="o",
            label=attack,
        )

    plt.xlabel("FGSM/PGD epsilon")
    plt.ylabel("Attack Success Rate")
    plt.title(
        "PhishVision Adversarial Attack Success Rate"
    )
    plt.ylim(0, 1)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    output = (
        OUTPUT_DIR
        / "attack_success_rate.png"
    )

    plt.savefig(
        output,
        dpi=200,
    )

    plt.close()

    print(f"Saved: {output}")


def plot_phishing_probability(
    data,
    clean_probability,
):
    plt.figure()

    for attack in ["FGSM", "PGD"]:
        plt.plot(
            data[attack]["epsilon"],
            data[attack]["probability"],
            marker="o",
            label=attack,
        )

    plt.axhline(
        clean_probability,
        linestyle="--",
        label="Clean",
    )

    plt.xlabel("FGSM/PGD epsilon")
    plt.ylabel(
        "Average phishing probability"
    )
    plt.title(
        "PhishVision Phishing Probability Under Attack"
    )
    plt.ylim(0, 1)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    output = (
        OUTPUT_DIR
        / "phishing_probability.png"
    )

    plt.savefig(
        output,
        dpi=200,
    )

    plt.close()

    print(f"Saved: {output}")


def plot_adversarial_recall(data):
    plt.figure()

    for attack in ["FGSM", "PGD"]:
        plt.plot(
            data[attack]["epsilon"],
            data[attack]["recall"],
            marker="o",
            label=attack,
        )

    plt.xlabel("FGSM/PGD epsilon")
    plt.ylabel(
        "Adversarial phishing recall"
    )
    plt.title(
        "PhishVision Adversarial Phishing Recall"
    )
    plt.ylim(0, 1)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    output = (
        OUTPUT_DIR
        / "adversarial_phishing_recall.png"
    )

    plt.savefig(
        output,
        dpi=200,
    )

    plt.close()

    print(f"Saved: {output}")


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Robustness CSV not found: {CSV_PATH}"
        )

    rows = load_results()

    data, clean_probability = aggregate(rows)

    print(
        f"Loaded {len(rows)} robustness records."
    )

    print(
        f"Average clean phishing probability: "
        f"{clean_probability:.4f}"
    )

    plot_attack_success_rate(data)
    plot_phishing_probability(
        data,
        clean_probability,
    )
    plot_adversarial_recall(data)

    print()
    print(
        f"Plots saved to: {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()