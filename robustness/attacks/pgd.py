import torch


def pgd_attack(
    model,
    images,
    labels,
    epsilon,
    alpha,
    steps,
    loss_fn=None,
):
    """
    Generate adversarial examples using Projected Gradient Descent (PGD).

    Perturbations are constrained to an L-infinity epsilon ball around
    the original image.

    Args:
        model: PyTorch classification model.
        images: Input image tensor in [0, 1], shape [N, C, H, W].
        labels: Ground-truth class labels.
        epsilon: Maximum per-pixel perturbation.
        alpha: Step size for each PGD iteration.
        steps: Number of gradient iterations.
        loss_fn: Loss function used for the input gradient.

    Returns:
        Adversarial image tensor clamped to [0, 1].
    """
    if loss_fn is None:
        loss_fn = torch.nn.CrossEntropyLoss()

    model.eval()

    original_images = images.detach().clone()

    # Start from the clean image.
    adversarial_images = original_images.clone().detach()

    for _ in range(steps):
        adversarial_images.requires_grad_(True)

        model.zero_grad(set_to_none=True)

        # Importantly, the model receives normalized images.
        mean = torch.tensor(
            [0.485, 0.456, 0.406],
            device=adversarial_images.device,
        ).view(1, 3, 1, 1)

        std = torch.tensor(
            [0.229, 0.224, 0.225],
            device=adversarial_images.device,
        ).view(1, 3, 1, 1)

        normalized = (adversarial_images - mean) / std

        outputs = model(normalized)
        loss = loss_fn(outputs, labels)

        loss.backward()

        gradient_sign = adversarial_images.grad.sign()

        adversarial_images = (
            adversarial_images.detach()
            + alpha * gradient_sign
        )

        # Project back into the epsilon L-infinity ball.
        perturbation = (
            adversarial_images - original_images
        ).clamp(
            min=-epsilon,
            max=epsilon,
        )

        adversarial_images = (
            original_images + perturbation
        ).clamp(
            min=0.0,
            max=1.0,
        ).detach()

    return adversarial_images